"""Path helper utilities for run engine modules."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Resolve repository root from this module location.

    Used by:
    - `src/ui/engine/paths.py` (self utilities)
    - `src/ui/engine/live_runtime.py`
    - `src/ui/engine/importing.py`
    """
    return Path(__file__).resolve().parents[3]


def src_dir() -> Path:
    """Resolve the `src` directory.

    Used by:
    - `src/ui/engine/live_runtime.py` for lazy `ChallengeEnv` import path injection.
    """
    return repo_root() / "src"


def resolve_dataset_path(dataset_path: str) -> Path:
    """Normalize a dataset path (absolute or relative) to absolute path.

    Used by:
    - `src/ui/engine/loaders.py`
    - `src/ui/engine/live_runtime.py`
    """
    candidate = Path(dataset_path)
    if candidate.is_absolute():
        return candidate
    return repo_root() / candidate
