"""Run history persistence."""

from __future__ import annotations

import json
import logging
from typing import Any

from .paths import RUNS_PATH, ensure_data_dir

logger = logging.getLogger(__name__)


def load_runs() -> list[dict[str, Any]]:
    """Load all persisted runs from disk. Returns [] on missing file or parse error."""
    ensure_data_dir()

    if not RUNS_PATH.exists():
        logger.debug("No runs file found at %s, returning empty list.", RUNS_PATH)
        return []

    try:
        with RUNS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load runs from %s: %s", RUNS_PATH, exc)
        return []

    if not isinstance(data, list):
        logger.warning("Runs file %s has unexpected format, returning empty list.", RUNS_PATH)
        return []

    logger.debug("Loaded %d runs from %s", len(data), RUNS_PATH)
    return data


def save_runs(runs: list[dict[str, Any]]) -> None:
    """Persist the full run list to disk."""
    ensure_data_dir()
    with RUNS_PATH.open("w", encoding="utf-8") as f:
        json.dump(runs, f, indent=2, ensure_ascii=False)
    logger.debug("Saved %d runs to %s", len(runs), RUNS_PATH)


def append_run(run: dict[str, Any]) -> None:
    """Append one run and persist."""
    runs = load_runs()
    runs.append(run)
    save_runs(runs)
    logger.info("Run '%s' (%s) appended to store.", run.get("name"), run.get("run_id"))
