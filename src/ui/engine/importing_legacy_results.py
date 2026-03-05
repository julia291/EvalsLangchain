"""Legacy results import helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .record_builder import build_run_record
from .paths import repo_root


def import_legacy_results_file(
    results_path: str,
    run_name: str | None = None,
    keyword: str = "boredom",
    target_injections: int = 0,
    max_flags: int = 8,
) -> dict:
    """Convert legacy result JSON into canonical run schema.

    Used by:
    - `src/ui/pages/3_Results.py`
    """
    path = Path(results_path)
    if not path.is_absolute():
        path = repo_root() / path

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("responses"), list):
        rows = payload["responses"]
    else:
        raise ValueError("Unsupported legacy results format.")

    inferred_name = run_name or f"import-{path.stem}"
    parameters = {
        "execution_mode": "legacy_import",
        "dataset_path": str(path),
        "keyword": keyword,
        "target_injections": target_injections,
        "max_flags": max_flags,
        "notes": "Imported from legacy results file.",
    }

    return build_run_record(
        run_name=inferred_name,
        parameters=parameters,
        rows=rows,
        total_mails=len(rows),
        source="legacy_import",
    )
