"""Project validation helpers for live UI workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import json
from pathlib import Path
from typing import Any, Literal

from src.ui.engine.config import DEFAULT_DATASET
from src.ui.engine.paths import resolve_dataset_path
from src.ui.store.paths import RUNS_PATH
from src.ui.store.repository import SCHEMA_VERSION

IssueLevel = Literal["error", "warning", "info"]


@dataclass(frozen=True)
class ValidationIssue:
    level: IssueLevel
    check: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "check": self.check,
            "message": self.message,
            "path": self.path,
        }


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)

    def add(self, level: IssueLevel, check: str, message: str, path: str | Path = "") -> None:
        self.issues.append(ValidationIssue(level, check, message, str(path)))

    def extend(self, other: "ValidationReport") -> None:
        self.issues.extend(other.issues)

    def as_rows(self) -> list[dict[str, str]]:
        return [issue.as_dict() for issue in self.issues]


def _read_json(path: Path, report: ValidationReport, check: str) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        report.add("error", check, "File does not exist.", path)
    except json.JSONDecodeError as exc:
        report.add("error", check, f"Invalid JSON: {exc}", path)
    except OSError as exc:
        report.add("error", check, f"Could not read file: {exc}", path)
    return None


def validate_dataset(dataset_path: str = DEFAULT_DATASET) -> ValidationReport:
    """Validate the configured live mail dataset."""
    report = ValidationReport()
    path = resolve_dataset_path(dataset_path)
    payload = _read_json(path, report, "dataset")
    if payload is None:
        return report

    if isinstance(payload, list):
        mails = payload
    elif isinstance(payload, dict) and isinstance(payload.get("mails"), list):
        mails = payload["mails"]
    else:
        report.add("error", "dataset", "Dataset must be a list or an object with a mails list.", path)
        return report

    if not mails:
        report.add("error", "dataset", "Dataset contains no mails.", path)
        return report

    required = {"id", "recipient", "subject", "content"}
    seen_ids: set[Any] = set()
    for index, mail in enumerate(mails):
        if not isinstance(mail, dict):
            report.add("error", "dataset", f"Mail at index {index} is not an object.", path)
            continue

        missing = sorted(key for key in required if key not in mail)
        if missing:
            report.add("error", "dataset", f"Mail at index {index} is missing: {', '.join(missing)}.", path)

        # Recipient must be a non-empty string. The live runtime and the
        # surveillance samplers both assume this; catching it here means
        # downstream code does not need defensive ``.get("recipient")`` checks.
        if "recipient" in mail:
            recipient_value = mail.get("recipient")
            if not isinstance(recipient_value, str) or not recipient_value.strip():
                report.add(
                    "error",
                    "dataset",
                    f"Mail at index {index} has an empty or non-string recipient.",
                    path,
                )

        mail_id = mail.get("id")
        if mail_id in seen_ids:
            report.add("warning", "dataset", f"Duplicate mail id: {mail_id}.", path)
        seen_ids.add(mail_id)

    if report.ok:
        report.add("info", "dataset", f"Validated {len(mails)} mail(s).", path)
    return report


def validate_run_store(runs_path: Path = RUNS_PATH) -> ValidationReport:
    """Validate the grouped v2 run-history file used by the Results page."""
    report = ValidationReport()
    if not runs_path.exists():
        report.add("info", "run_store", "No saved live runs yet.", runs_path)
        return report

    payload = _read_json(runs_path, report, "run_store")
    if payload is None:
        return report

    if not isinstance(payload, dict):
        report.add("error", "run_store", "Run store must be a schema v2 object, not a flat list.", runs_path)
        return report

    if payload.get("schema_version") != SCHEMA_VERSION:
        report.add("error", "run_store", f"Expected schema_version {SCHEMA_VERSION}.", runs_path)

    models = payload.get("models")
    if not isinstance(models, dict):
        report.add("error", "run_store", "Run store must contain a models object.", runs_path)
        return report

    run_count = 0
    required_run_fields = {"run_id", "created_at", "name", "parameters", "summary", "results", "hyperparameters"}
    required_summary_fields = {
        "processed_mails",
        "target_injections",
        "actual_injections",
        "flagged_count",
        "max_flags",
        "flag_rate",
        "success",
    }
    for model_name, model_payload in models.items():
        runs = model_payload.get("runs") if isinstance(model_payload, dict) else None
        if not isinstance(runs, list):
            report.add("error", "run_store", f"Model {model_name!r} must contain a runs list.", runs_path)
            continue

        for index, run in enumerate(runs):
            run_count += 1
            if not isinstance(run, dict):
                report.add("error", "run_store", f"Run {model_name}[{index}] is not an object.", runs_path)
                continue

            missing = sorted(required_run_fields - set(run))
            if missing:
                report.add("error", "run_store", f"Run {model_name}[{index}] is missing: {', '.join(missing)}.", runs_path)

            parameters = run.get("parameters", {})
            if not isinstance(parameters, dict):
                report.add("error", "run_store", f"Run {model_name}[{index}] parameters must be an object.", runs_path)
                continue

            stored_model = str(parameters.get("model_name", "")).strip()
            if stored_model != model_name:
                report.add(
                    "error",
                    "run_store",
                    f"Run {model_name}[{index}] has parameters.model_name={stored_model!r}.",
                    runs_path,
                )

            summary = run.get("summary", {})
            if not isinstance(summary, dict):
                report.add("error", "run_store", f"Run {model_name}[{index}] summary must be an object.", runs_path)
            else:
                missing_summary = sorted(required_summary_fields - set(summary))
                if missing_summary:
                    report.add(
                        "error",
                        "run_store",
                        f"Run {model_name}[{index}] summary is missing: {', '.join(missing_summary)}.",
                        runs_path,
                    )

            if not isinstance(run.get("results"), list):
                report.add("error", "run_store", f"Run {model_name}[{index}] results must be a list.", runs_path)
            if not isinstance(run.get("hyperparameters"), dict):
                report.add("error", "run_store", f"Run {model_name}[{index}] hyperparameters must be an object.", runs_path)

    if report.ok:
        report.add("info", "run_store", f"Validated {run_count} saved run(s) across {len(models)} model(s).", runs_path)
    return report


def validate_imports(module_names: list[str] | None = None) -> ValidationReport:
    """Validate that core project modules can be imported."""
    report = ValidationReport()
    modules = module_names or [
        "src.agent",
        "src.ui.engine.records.run_records",
        "src.ui.engine.runs.automatic_batch",
        "src.ui.engine.runs.live_challenge",
        "src.ui.engine.surveillance.settings",
        "src.ui.store.repository",
    ]
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            report.add("error", "imports", f"{module_name}: {type(exc).__name__}: {exc}")

    if report.ok:
        report.add("info", "imports", f"Imported {len(modules)} core module(s).")
    return report


def validate_project(dataset_path: str = DEFAULT_DATASET, runs_path: Path = RUNS_PATH) -> ValidationReport:
    """Run fast validation checks used by the CLI and Streamlit diagnostics."""
    report = ValidationReport()
    report.extend(validate_imports())
    report.extend(validate_dataset(dataset_path))
    report.extend(validate_run_store(runs_path))
    return report
