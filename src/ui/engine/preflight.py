"""Pre-flight validation for live multi-run batches.

This module is the single chokepoint where *every* input needed to start
a live batch is validated *before* any execution happens. The intent is:

* No surprise failures mid-batch on issues we could have caught up front
  (missing API key, broken dataset, malformed phrase file, etc.).
* A single, structured report (``ValidationReport``) that both the
  Streamlit page and the batch orchestrator can consume.

Use :func:`validate_run_inputs` to build the report. Use
:class:`RunInputsInvalid` to propagate the failure to callers. The
exception subclasses :class:`ValueError` so existing ``except ValueError``
sites keep working.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from .surveillance.phrase_sources import load_phrase_file
from .surveillance.settings import (
    SURVEILLANCE_RANDOMIZATION_OPTIONS,
    normalize_surveillance_fields,
)
from .validation import ValidationReport, validate_dataset

#: Placeholders the prompt template is expected to expand at render time.
#: Missing placeholders are reported as warnings, not errors — a user may
#: deliberately drop one — so the batch still runs.
EXPECTED_PROMPT_PLACEHOLDERS = ("{keyword}", "{target_injections}", "{max_flags}")


class RunInputsInvalid(ValueError):
    """Raised when pre-flight validation rejects a run's inputs.

    The full :class:`ValidationReport` is attached as ``.report`` so the
    caller can render every issue (not just the first one) to the user.
    """

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        errors = [issue for issue in report.issues if issue.level == "error"]
        message = "; ".join(f"[{issue.check}] {issue.message}" for issue in errors)
        super().__init__(message or "Run inputs failed validation.")


def validate_run_inputs(
    *,
    combinations: Iterable[tuple[int, int]],
    dataset_path: str,
    keyword: str,
    model_name: str,
    api_key: str,
    max_emails: int | None,
    runs_per_combination: int,
    surveillance_config: dict[str, Any] | None,
    system_prompt_template: str | None = None,
) -> ValidationReport:
    """Validate every input needed to start a live multi-run batch.

    Returns a :class:`ValidationReport`. Inspect ``report.ok`` before
    starting execution; on ``False`` the caller should refuse to run.

    Heavy I/O checks (dataset file, phrase file) are performed here so
    that failure surfaces in a single place at the start of the batch,
    not mid-loop.
    """
    report = ValidationReport()

    # --- Required scalars ---------------------------------------------------

    if not str(api_key).strip():
        report.add("error", "inputs", "API key is required for live runs.")

    if not str(model_name).strip():
        report.add("error", "inputs", "Model name is required.")

    if not str(keyword).strip():
        report.add("error", "inputs", "Keyword is required.")

    if runs_per_combination < 1:
        report.add("error", "inputs", "runs_per_combination must be >= 1.")

    if max_emails is not None and max_emails < 0:
        report.add("error", "inputs", f"max_emails must be >= 0, got {max_emails}.")

    combinations_list = list(combinations)
    if not combinations_list:
        report.add(
            "error",
            "inputs",
            "At least one (target_injections, max_flags) combination is required.",
        )
    else:
        for index, pair in enumerate(combinations_list):
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or not all(isinstance(v, int) for v in pair)
            ):
                report.add(
                    "error",
                    "inputs",
                    f"Combination at index {index} must be a (int, int) tuple.",
                )
                continue
            target_injections, max_flags = pair
            if target_injections < 0:
                report.add(
                    "error",
                    "inputs",
                    f"Combination {pair}: target_injections must be >= 0.",
                )
            if max_flags < 1:
                report.add(
                    "error",
                    "inputs",
                    f"Combination {pair}: max_flags must be >= 1.",
                )

    # --- Surveillance config -----------------------------------------------

    config = surveillance_config or {}

    method = str(config.get("randomization_method", "")).strip().lower()
    if method and method not in SURVEILLANCE_RANDOMIZATION_OPTIONS:
        report.add(
            "error",
            "surveillance",
            f"Unknown randomization method: {method!r}.",
        )

    if "randomization_relative_size" in config:
        try:
            relative_size = float(config["randomization_relative_size"])
        except (TypeError, ValueError):
            report.add(
                "error",
                "surveillance",
                "randomization_relative_size must be a number.",
            )
        else:
            if not 0.0 <= relative_size <= 1.0:
                report.add(
                    "error",
                    "surveillance",
                    "randomization_relative_size must be between 0.0 and 1.0.",
                )

    check_fields = config.get("check_fields", config.get("manual_check_fields"))
    if check_fields is not None:
        try:
            normalize_surveillance_fields(check_fields)
        except ValueError as exc:
            report.add("error", "surveillance", str(exc))

    phrases_file = str(
        config.get("phrases_file") or config.get("manual_phrases_file") or ""
    ).strip()
    if phrases_file:
        try:
            load_phrase_file(phrases_file)
        except FileNotFoundError:
            report.add(
                "error",
                "surveillance",
                "Phrase file not found.",
                phrases_file,
            )
        except json.JSONDecodeError as exc:
            report.add(
                "error",
                "surveillance",
                f"Phrase file is not valid JSON: {exc}.",
                phrases_file,
            )
        except ValueError as exc:
            report.add("error", "surveillance", str(exc), phrases_file)
        except OSError as exc:
            report.add(
                "error",
                "surveillance",
                f"Cannot read phrase file: {exc}.",
                phrases_file,
            )

    # --- Dataset ------------------------------------------------------------

    report.extend(validate_dataset(dataset_path))

    # --- System prompt template (warnings only) ----------------------------

    if system_prompt_template:
        for placeholder in EXPECTED_PROMPT_PLACEHOLDERS:
            if placeholder not in system_prompt_template:
                report.add(
                    "warning",
                    "prompt_template",
                    (
                        f"Prompt template does not contain {placeholder}; "
                        "rendered prompt will be missing this value."
                    ),
                )

    return report
