"""Facade module for run-history storage.

Why this file still exists:
- Existing pages import from `src.ui.run_store`.
- Storage internals are now split into categorized modules under `src/ui/store/`.
"""

from __future__ import annotations

try:
    # Package-style imports (normal app execution path).
    from src.ui.store.paths import DATA_DIR, REPO_ROOT, RUNS_PATH, ensure_data_dir as _ensure_data_dir
    from src.ui.store.repository import append_run, load_runs, save_runs
except ModuleNotFoundError:
    # Local fallback imports (when `src` package path is not available).
    from store.paths import DATA_DIR, REPO_ROOT, RUNS_PATH, ensure_data_dir as _ensure_data_dir
    from store.repository import append_run, load_runs, save_runs

__all__ = [
    "REPO_ROOT",
    "DATA_DIR",
    "RUNS_PATH",
    "_ensure_data_dir",
    "load_runs",
    "save_runs",
    "append_run",
]
