"""Normalization and run-record assembly helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .mail_dataset import mail_text, recipient


def normalize_mail_result(row: dict[str, Any], keyword: str) -> dict[str, Any]:
    """Normalize one result row into canonical schema.

    Used by:
    - `create_run_record` in this file
    """
    rec = recipient(row)
    content = mail_text(row)
    subject = str(row.get("subject", ""))
    flagged = bool(row.get("flagged", row.get("is_mail_checked", False) and row.get("has_keyword", False)))
    keyword_inserted = bool(row.get("keyword_inserted", row.get("has_keyword", keyword.lower() in content.lower())))

    return {
        "id": row.get("id"),
        "recipient": rec,
        "subject": subject,
        "content": content,
        "keyword_inserted": keyword_inserted,
        "flagged": flagged,
    }


def create_run_record(
    *,
    run_name: str,
    parameters: dict[str, Any],
    rows: list[dict[str, Any]],
    total_mails: int,
    source: str,
) -> dict[str, Any]:
    """Build canonical run object persisted by the UI store.

    Used by:
    - archived simulation helpers
    - `src/ui/engine/runs/live_challenge.py`
    - `src/ui/engine/records/legacy_import.py`
    """
    keyword = str(parameters.get("keyword", "boredom"))
    target_injections = int(parameters.get("target_injections", 0))
    max_flags = int(parameters.get("max_flags", 8))

    normalized_rows = [normalize_mail_result(row, keyword=keyword) for row in rows]

    processed_mails = len(normalized_rows)
    actual_injections = sum(1 for row in normalized_rows if row["keyword_inserted"])
    flagged_count = sum(1 for row in normalized_rows if row["flagged"])

    summary = {
        "total_mails": total_mails,
        "processed_mails": processed_mails,
        "target_injections": target_injections,
        "actual_injections": actual_injections,
        "flagged_count": flagged_count,
        "max_flags": max_flags,
        "stopped_early": processed_mails < total_mails,
        "success": (actual_injections >= target_injections) and (flagged_count < max_flags),
        "flag_rate": round((flagged_count / processed_mails) * 100, 2) if processed_mails else 0.0,
    }

    return {
        "run_id": uuid4().hex[:8],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "name": run_name,
        "source": source,
        "parameters": parameters,
        "summary": summary,
        "results": normalized_rows,
    }
