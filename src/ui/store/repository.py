"""Run history repository helpers."""

from __future__ import annotations

import json
from typing import Any

from .paths import RUNS_PATH, ensure_data_dir


def load_runs() -> list[dict[str, Any]]:
    """Load all persisted runs from disk.

    Used by:
    - `src/ui/pages/results.py`
    - `append_run` in this file
    """
    ensure_data_dir()

    if not RUNS_PATH.exists():
        return []

    try:
        with RUNS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return data


def save_runs(runs: list[dict[str, Any]]) -> None:
    """Persist the full run list to disk.

    Used by:
    - `append_run` in this file
    """
    ensure_data_dir()
    with RUNS_PATH.open("w", encoding="utf-8") as f:
        json.dump(runs, f, indent=2, ensure_ascii=False)


def append_run(run: dict[str, Any]) -> None:
    """Append one run and save updated repository state.

    Used by:
    - `src/ui/pages/multiple_runs.py`
    - `src/ui/pages/results.py` (legacy import path)
    """
    runs = load_runs()
    runs.append(run)
    save_runs(runs)
