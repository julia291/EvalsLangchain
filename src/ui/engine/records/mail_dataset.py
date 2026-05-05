"""Data loading helper functions for run execution."""

from __future__ import annotations

import json
from typing import Any

from ..paths import resolve_dataset_path


def load_mails(dataset_path: str) -> list[dict[str, Any]]:
    """Load mails from supported JSON shapes.

    Used by:
    - archived simulation helpers
    - `src/ui/engine/runs/live_challenge.py`
    """
    resolved = resolve_dataset_path(dataset_path)
    with resolved.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "mails" in payload and isinstance(payload["mails"], list):
        return payload["mails"]

    raise ValueError("Unsupported dataset format.")


def recipient(mail: dict[str, Any]) -> str:
    """Read recipient field with compatibility fallback.

    Used by:
    - `src/ui/engine/normalization.py`
    - archived simulation helpers
    """
    return str(mail.get("recipient") or mail.get("empfänger") or "")


def mail_text(mail: dict[str, Any]) -> str:
    """Read message text from common content fields.

    Used by:
    - `src/ui/engine/normalization.py`
    - archived simulation helpers
    """
    return str(mail.get("content") or mail.get("text") or "")
