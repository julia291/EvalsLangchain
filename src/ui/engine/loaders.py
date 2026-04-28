"""Mail data loading helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

from .paths import resolve_dataset_path

logger = logging.getLogger(__name__)


def load_mails(dataset_path: str) -> list[dict[str, Any]]:
    """Load mails from a JSON file (list or {mails: [...]} format)."""
    resolved = resolve_dataset_path(dataset_path)
    logger.debug("Loading mails from %s", resolved)
    with resolved.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        logger.info("Loaded %d mails from %s", len(payload), resolved)
        return payload
    if isinstance(payload, dict) and "mails" in payload and isinstance(payload["mails"], list):
        logger.info("Loaded %d mails from %s", len(payload["mails"]), resolved)
        return payload["mails"]

    raise ValueError(f"Unsupported dataset format in {resolved}.")


def recipient(mail: dict[str, Any]) -> str:
    """Read recipient field with legacy-key fallback."""
    return str(mail.get("recipient") or mail.get("empfänger") or "")


def mail_text(mail: dict[str, Any]) -> str:
    """Read message body from common content fields."""
    return str(mail.get("content") or mail.get("text") or "")
