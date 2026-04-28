"""Storage path helpers for run repository."""

from __future__ import annotations

from pathlib import Path

# Used by: `src/ui/store/repository.py`
# Why: centralize data file location so it is defined once.
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RUNS_PATH = DATA_DIR / "ui_runs.json"


def ensure_data_dir() -> None:
    """Ensure run-history directory exists before read/write operations.

    Used by:
    - `src/ui/store/repository.py`
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
