"""Loaders and normalizers for surveillance phrase lists.

Three input shapes feed into the live surveillance rule:

* Inline phrases the user typed into the Multiple Runs page.
* A JSON phrase file pointed at via path.
* Dataset-derived random samples (see ``random_phrases.py``).

All three pass through :func:`deduplicate_phrase_values` so the final
runtime phrase list is lowercase, stripped, and free of duplicates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ..paths import repo_root


def deduplicate_phrase_values(values: Iterable[Any]) -> list[str]:
    """Return lowercased non-empty values with duplicates removed.

    Input order is preserved (stable de-duplication). Non-string values
    are stringified via ``str(...)`` before normalization, so callers can
    safely pass iterables of mixed types.
    """
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
