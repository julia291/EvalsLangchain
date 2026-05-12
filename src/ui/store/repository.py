"""Run history repository helpers.

Persists live runs to ``data/ui_runs.json`` using the schema-v2 grouped
layout::

    {
      "schema_version": 2,
      "models": {
        "<model-name>": {"runs": [<run record>, ...]}
      }
    }

Each saved run has a flattened ``hyperparameters`` map derived from its
``parameters`` block, which lets the Results page filter and chart on
arbitrary nested fields (for example ``surveillance.check_fields``).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any

from .paths import RUNS_PATH, ensure_data_dir

logger = logging.getLogger(__name__)

#: Persisted run-store schema version. Older flat-list stores are not
#: migrated automatically; see ``src/ui/engine/validation.py``.
SCHEMA_VERSION = 2


def _empty_store() -> dict[str, Any]:
    """Return a fresh, valid schema-v2 store with no runs."""
    return {"schema_version": SCHEMA_VERSION, "models": {}}


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dicts using dot-paths; non-dicts become leaves.

    Lists are kept as-is (the Results page renders them via JSON dumps).
    Used to build the ``hyperparameters`` map.
    """
    if not isinstance(value, dict):
        return {prefix: value} if prefix else {}

    flattened: dict[str, Any] = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, dict):
            flattened.update(_flatten(item, path))
        else:
            flattened[path] = item
    return flattened


def _prepare_run(run: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``run`` with a normalized ``model_name`` and a
    freshly computed ``hyperparameters`` map.

    Raises:
        ValueError: If ``parameters.model_name`` is missing or empty. The
            Results page groups by model, so this is a hard requirement.
    """
    prepared = dict(run)
    parameters = dict(prepared.get("parameters", {}))
    model_name = str(parameters.get("model_name", "")).strip()
    if not model_name:
        raise ValueError("Live run is missing parameters.model_name.")

    parameters["model_name"] = model_name
    prepared["parameters"] = parameters
    prepared["hyperparameters"] = _flatten(parameters)
    return prepared


def _group_by_model(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """Group prepared runs into the schema-v2 store shape."""
    store = _empty_store()
    models = store["models"]
    for run in runs:
        prepared = _prepare_run(run)
        model_name = prepared["parameters"]["model_name"]
        models.setdefault(model_name, {"runs": []})["runs"].append(prepared)
    return store


def _ungroup(store: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every run in a schema-v2 store as a flat list.

    Returns an empty list if the store is not the expected shape so the UI
    degrades gracefully; the validator in
    ``src/ui/engine/validation.py`` is the surface that reports problems.
    """
    models = store.get("models", {})
    if store.get("schema_version") != SCHEMA_VERSION or not isinstance(models, dict):
        return []

    runs: list[dict[str, Any]] = []
    for model in models.values():
        if isinstance(model, dict) and isinstance(model.get("runs"), list):
            runs.extend(run for run in model["runs"] if isinstance(run, dict))
    return runs


def load_runs() -> list[dict[str, Any]]:
    """Load all persisted live runs from disk.

    Returns an empty list if the file does not exist or cannot be read.
    Corrupt or unexpected file contents are logged (not raised) so the
    Streamlit Results page never crashes on a bad file; run validation via
    ``scripts/validate_project.py`` to inspect the underlying issue.
    """
    ensure_data_dir()

    if not RUNS_PATH.exists():
        return []

    try:
        with RUNS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.warning("Run store is not valid JSON (%s): %s", RUNS_PATH, exc)
        return []
    except OSError as exc:
        logger.warning("Cannot read run store (%s): %s", RUNS_PATH, exc)
        return []

    if not isinstance(data, dict):
        logger.warning("Run store has unexpected top-level shape: %s", RUNS_PATH)
        return []

    return _ungroup(data)


def save_runs(runs: list[dict[str, Any]]) -> None:
    """Persist runs grouped by model name.

    Writes atomically: the new content is written to a sibling temp file
    and then renamed over the destination. A crash mid-write therefore
    leaves the previous valid file in place rather than truncating it.
    """
    ensure_data_dir()
    payload = _group_by_model(runs)

    directory = RUNS_PATH.parent
    fd, tmp_path = tempfile.mkstemp(
        prefix=RUNS_PATH.name + ".",
        suffix=".tmp",
        dir=str(directory),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, RUNS_PATH)
    except Exception:
        # Best-effort cleanup of the orphan temp file; do not mask the
        # original error.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def append_run(run: dict[str, Any]) -> None:
    """Append one live run and save updated repository state."""
    runs = load_runs()
    runs.append(run)
    save_runs(runs)
