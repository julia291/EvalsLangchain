"""Path helper utilities for run engine modules."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Resolve repository root from this module location.

    Used by:
    - `src/ui/engine/paths.py` (self utilities)
    - `src/ui/engine/runs/live_challenge.py`
    - `src/ui/engine/importing.py`
    """
    return Path(__file__).resolve().parents[3]


def resolve_dataset_path(dataset_path: str) -> Path:
    """Normalize a dataset path (absolute or relative) to absolute path.

    Used by:
    - `src/ui/engine/records/mail_dataset.py`
    - `src/ui/engine/runs/live_challenge.py`
    """
    candidate = Path(dataset_path)
    if candidate.is_absolute():
        return candidate
    return repo_root() / candidate
