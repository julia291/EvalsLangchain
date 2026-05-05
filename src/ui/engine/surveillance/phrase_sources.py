"""General-purpose helpers shared by UI engine modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..paths import repo_root


def deduplicate_phrase_values(values: list[str] | tuple[str, ...] | Any) -> list[str]:
    """Return lowercased non-empty values with duplicates removed."""
    unique: list[str] = []
    for value in values:
        text = str(value).strip().lower()
        if not text or text in unique:
            continue
        unique.append(text)
    return unique


def parse_inline_phrase_text(raw: str) -> list[str]:
    """Parse comma/newline separated inline phrases from the UI."""
    if not raw.strip():
        return []

    parts = raw.replace("\r", "\n").replace(",", "\n").split("\n")
    return deduplicate_phrase_values(parts)


def load_phrase_file(file_path: str) -> list[str]:
    """Load a JSON phrase list from disk."""
    candidate = file_path.strip()
    if not candidate:
        return []

    path = Path(candidate)
    if not path.is_absolute():
        path = repo_root() / path

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        return deduplicate_phrase_values(str(item) for item in payload)

    if isinstance(payload, dict):
        for key in ("phrases", "values", "items"):
            values = payload.get(key)
            if isinstance(values, list):
                return deduplicate_phrase_values(str(item) for item in values)

    raise ValueError("Phrase file must be a JSON list or an object with a list field such as 'phrases'.")
