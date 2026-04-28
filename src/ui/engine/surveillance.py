"""Surveillance configuration and mail scanning."""

from __future__ import annotations

import logging
from typing import Any

from .helpers import load_phrases_from_file, parse_inline_phrases, unique_non_empty
from .randomization import _build_randomized_phrases

logger = logging.getLogger(__name__)

DEFAULT_SURVEILLANCE_RELATIVE_SIZE = 0.3
SURVEILLANCE_FIELD_OPTIONS = ["recipient", "subject"]
SURVEILLANCE_RANDOMIZATION_OPTIONS = {
    "none": "None",
    "whole_recipient": "Full recipient address",
    "recipient_name": "Recipient local part",
    "recipient_domain": "Recipient domain",
    "recipient_tld": "Recipient TLD",
}


def build_surveillance_config(
    *,
    randomization_method: str = "whole_recipient",
    randomization_relative_size: float = DEFAULT_SURVEILLANCE_RELATIVE_SIZE,
    manual_check_fields: list[str] | None = None,
    manual_phrases_file: str = "",
    manual_inline_phrases: str = "",
    mails: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a surveillance configuration dict from UI inputs.

    Without `mails`: returns the transport config (no phrases resolved).
    With `mails`: also resolves the final phrase list for the runtime.
    """
    normalized_method = str(randomization_method).strip().lower()
    if normalized_method not in SURVEILLANCE_RANDOMIZATION_OPTIONS:
        raise ValueError(f"Unsupported surveillance randomization method: {randomization_method}")

    relative_size = float(randomization_relative_size)
    if not 0.0 <= relative_size <= 1.0:
        raise ValueError("Surveillance randomization size must be between 0.0 and 1.0.")

    check_fields = normalize_check_fields(manual_check_fields)
    base_config: dict[str, Any] = {
        "randomization_method": normalized_method,
        "randomization_relative_size": relative_size,
        "check_fields": check_fields,
        "phrases_file": manual_phrases_file.strip(),
        "inline_phrases": manual_inline_phrases,
    }

    if mails is None:
        logger.debug("Surveillance config built (no phrases resolved): fields=%s, method=%s",
                     check_fields, normalized_method)
        return base_config

    file_phrases = load_phrases_from_file(base_config["phrases_file"])
    inline_phrases = parse_inline_phrases(base_config["inline_phrases"])
    generated_phrases = (
        []
        if normalized_method == "none"
        else _build_randomized_phrases(mails=mails, method=normalized_method, relative_size=relative_size)
    )
    phrases = unique_non_empty([*file_phrases, *inline_phrases, *generated_phrases])

    if not phrases:
        logger.warning("Surveillance resolved 0 phrases — no mails will be scanned.")

    logger.info("Surveillance phrases resolved: %d total (file=%d, inline=%d, generated=%d)",
                len(phrases), len(file_phrases), len(inline_phrases), len(generated_phrases))

    return {**base_config, "phrases": phrases, "phrase_count": len(phrases)}


def normalize_check_fields(check_fields: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Normalize check-field input to a validated, deduplicated list.

    Accepts: None, a single string ("recipient", "subject", "both"), or a list.
    "both" expands to ["recipient", "subject"].
    """
    if check_fields is None:
        return ["recipient"]

    if isinstance(check_fields, str):
        value = check_fields.strip().lower()
        if not value:
            return []
        if value == "both":
            return ["recipient", "subject"]
        raw_fields = [value]
    else:
        raw_fields = [str(field).strip().lower() for field in check_fields if str(field).strip()]

    fields: list[str] = []
    for field in raw_fields:
        if field not in SURVEILLANCE_FIELD_OPTIONS:
            raise ValueError(f"Unsupported surveillance field: {field}")
        if field not in fields:
            fields.append(field)
    return fields


def should_scan_mail(
    *, mail: dict[str, Any], check_fields: list[str], phrases: list[str]
) -> tuple[bool, str | None, str | None]:
    """Return (should_scan, matched_field, matched_phrase) for a given mail.

    Returns (False, None, None) if no phrase matches any checked field.
    """
    for field in check_fields:
        value = str(mail.get(field, ""))
        for phrase in phrases:
            if phrase.lower() in value.lower():
                logger.debug("Mail matched: field=%s, phrase=%s", field, phrase)
                return True, field, phrase
    return False, None, None
