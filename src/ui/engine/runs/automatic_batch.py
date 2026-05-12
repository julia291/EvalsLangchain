"""Automatic live multi-run orchestration.

This module owns the batch execution loop used by the Streamlit "Multiple Runs"
page. Keeping it outside the page makes the behavior easy to test without
launching Streamlit or calling a live model.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from .live_prompts import render_live_prompt

logger = logging.getLogger(__name__)

RunCallable = Callable[..., dict[str, Any]]
SaveRunCallable = Callable[[dict[str, Any]], None]
ProgressCallback = Callable[[int, int, str], None]


@dataclass(frozen=True)
class AutomaticRunFailure:
    """Serializable failure metadata for one attempted automatic run."""

    run_name: str
    target_injections: int
    max_flags: int
    repetition: int
    runs_per_combination: int
    error: str

    def as_row(self) -> dict[str, str | int]:
        """Return a UI-friendly row for Streamlit dataframes."""
        return {
            "run_name": self.run_name,
            "target_injections": self.target_injections,
            "max_flags": self.max_flags,
            "repetition": f"{self.repetition}/{self.runs_per_combination}",
            "error": self.error,
        }


@dataclass(frozen=True)
class AutomaticBatchResult:
    """Outcome of an automatic live multi-run batch."""

    created: list[dict[str, Any]]
    failures: list[AutomaticRunFailure]

    @property
    def failure_rows(self) -> list[dict[str, str | int]]:
        """Return failures in a UI-friendly shape."""
        return [failure.as_row() for failure in self.failures]


def format_automatic_run_name(
    *,
    prefix: str,
    target_injections: int,
    max_flags: int,
    repetition: int,
) -> str:
    """Build a stable run name that encodes the sweep dimensions."""
    clean_prefix = prefix.strip() or "auto-live"
    return f"{clean_prefix}-t{target_injections}-f{max_flags}-r{repetition}"


def format_automatic_run_notes(
    *,
    notes: str,
    target_injections: int,
    max_flags: int,
    repetition: int,
    runs_per_combination: int,
) -> str:
    """Attach machine-readable automatic-run metadata to user notes."""
    return (
        f"{notes}\n"
        f"auto.target_injections={target_injections}\n"
        f"auto.max_flags={max_flags}\n"
        f"auto.repetition={repetition}/{runs_per_combination}"
    ).strip()


def build_run_summary_table(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a compact comparison table for completed automatic runs."""
    return [
        {
            "run_id": run["run_id"],
            "name": run["name"],
            "target_injections": run.get("parameters", {}).get("target_injections"),
            "max_flags": run.get("parameters", {}).get("max_flags"),
            "processed": run["summary"]["processed_mails"],
            "injections": run["summary"]["actual_injections"],
            "flags": run["summary"]["flagged_count"],
            "flag_rate": run["summary"]["flag_rate"],
            "success": run["summary"]["success"],
        }
        for run in runs
    ]


def run_automatic_live_batch(
    *,
    run_name_prefix: str,
    combinations: list[tuple[int, int]],
    runs_per_combination: int,
    dataset_path: str,
    keyword: str,
    model_name: str,
    api_key: str,
    surveillance_config: dict[str, Any],
    system_prompt_template: str,
    max_emails: int | None,
    notes: str,
    run_live: RunCallable,
    save_run: SaveRunCallable,
    progress_callback: ProgressCallback | None = None,
) -> AutomaticBatchResult:
    """Execute and persist every run in an automatic live sweep.

    Inputs are expected to be pre-validated by the caller. The
    Streamlit "Multiple Runs" page calls
    :func:`src.ui.engine.preflight.validate_run_inputs` before invoking
    this function; direct callers (scripts, tests) should do the same
    if they want a clean failure on bad inputs.

    Failures during individual runs are logged and captured but do not
    stop the batch. Each successful run is persisted immediately
    through ``save_run``.
    """
    total_runs = len(combinations) * runs_per_combination
    logger.info(
        "automatic_batch_started",
        extra={
            "total_runs": total_runs,
            "combination_count": len(combinations),
            "runs_per_combination": runs_per_combination,
        },
    )

    created: list[dict[str, Any]] = []
    failures: list[AutomaticRunFailure] = []
    completed = 0

    for target_injections, max_flags in combinations:
        for repetition in range(1, runs_per_combination + 1):
            completed += 1
            run_name = format_automatic_run_name(
                prefix=run_name_prefix,
                target_injections=target_injections,
                max_flags=max_flags,
                repetition=repetition,
            )
            logger.info(
                "automatic_run_started",
                extra={
                    "run_name": run_name,
                    "completed": completed,
                    "total_runs": total_runs,
                    "target_injections": target_injections,
                    "max_flags": max_flags,
                    "repetition": repetition,
                },
            )

            if progress_callback is not None:
                progress_callback(completed - 1, total_runs, run_name)

            run_prompt = render_live_prompt(
                prompt_template=system_prompt_template,
                keyword=keyword,
                target_injections=target_injections,
                max_flags=max_flags,
            )
            run_notes = format_automatic_run_notes(
                notes=notes,
                target_injections=target_injections,
                max_flags=max_flags,
                repetition=repetition,
                runs_per_combination=runs_per_combination,
            )

            try:
                run = run_live(
                    run_name=run_name,
                    dataset_path=dataset_path,
                    keyword=keyword,
                    target_injections=target_injections,
                    max_flags=max_flags,
                    model_name=model_name,
                    api_key=api_key,
                    surveillance_config=surveillance_config,
                    system_prompt=run_prompt,
                    max_emails=max_emails,
                    notes=run_notes,
                )
                save_run(run)
                created.append(run)
                logger.info("automatic_run_saved", extra={"run_name": run_name})
            except Exception as exc:
                logger.exception("automatic_run_failed", extra={"run_name": run_name})
                failures.append(
                    AutomaticRunFailure(
                        run_name=run_name,
                        target_injections=target_injections,
                        max_flags=max_flags,
                        repetition=repetition,
                        runs_per_combination=runs_per_combination,
                        error=str(exc),
                    )
                )

            if progress_callback is not None:
                progress_callback(completed, total_runs, run_name)

    logger.info(
        "automatic_batch_finished",
        extra={
            "created_count": len(created),
            "failure_count": len(failures),
            "total_runs": total_runs,
        },
    )
    return AutomaticBatchResult(created=created, failures=failures)
