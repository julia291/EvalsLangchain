"""Data loading helper functions for live run execution."""

from __future__ import annotations

import json
from typing import Any

from ..paths import resolve_dataset_path


def load_mails(dataset_path: str) -> list[dict[str, Any]]:
    """Load mails from the live-run dataset JSON."""
    resolved = resolve_dataset_path(dataset_path)
    with resolved.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("mails"), list):
        return payload["mails"]

    raise ValueError("Unsupported dataset format.")


def recipient(mail: dict[str, Any]) -> str:
    """Read the live dataset recipient field."""
    return str(mail.get("recipient") or "")


def mail_text(mail: dict[str, Any]) -> str:
    """Read the live dataset message text field."""
    return str(mail.get("content") or "")
