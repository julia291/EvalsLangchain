"""Run history repository helpers."""

from __future__ import annotations

import json
from typing import Any

from .paths import RUNS_PATH, ensure_data_dir

SCHEMA_VERSION = 2


def _empty_store() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "models": {}}


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
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
    store = _empty_store()
    models = store["models"]
    for run in runs:
        prepared = _prepare_run(run)
        model_name = prepared["parameters"]["model_name"]
        models.setdefault(model_name, {"runs": []})["runs"].append(prepared)
    return store


def _ungroup(store: dict[str, Any]) -> list[dict[str, Any]]:
    models = store.get("models", {})
    if store.get("schema_version") != SCHEMA_VERSION or not isinstance(models, dict):
        return []

    runs: list[dict[str, Any]] = []
    for model in models.values():
        if isinstance(model, dict) and isinstance(model.get("runs"), list):
            runs.extend(run for run in model["runs"] if isinstance(run, dict))
    return runs


def load_runs() -> list[dict[str, Any]]:
    """Load all persisted live runs from disk."""
    ensure_data_dir()

    if not RUNS_PATH.exists():
        return []

    try:
        with RUNS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, dict):
        return []

    return _ungroup(data)


def save_runs(runs: list[dict[str, Any]]) -> None:
    """Persist runs grouped by model name."""
    ensure_data_dir()
    with RUNS_PATH.open("w", encoding="utf-8") as f:
        json.dump(_group_by_model(runs), f, indent=2, ensure_ascii=False)


def append_run(run: dict[str, Any]) -> None:
    """Append one live run and save updated repository state."""
    runs = load_runs()
    runs.append(run)
    save_runs(runs)
