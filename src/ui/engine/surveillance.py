"""Helpers for configuring the live surveillance system.

This module keeps the UI-facing configuration object small and serializable.
When mail rows are provided, it also resolves the runtime phrase list used by
the live challenge.
"""

from __future__ import annotations

from typing import Any

from .helpers import load_phrases_from_file, parse_inline_phrases, unique_non_empty
from .randomization import _build_randomized_phrases

DEFAULT_SURVEILLANCE_RELATIVE_SIZE = 0.3  # Default fraction of dataset-derived phrases used in randomization mode.
SURVEILLANCE_FIELD_OPTIONS = ["recipient", "subject"]  # Outgoing fields that the surveillance rule can inspect.
SURVEILLANCE_RANDOMIZATION_OPTIONS = {  # User-facing mapping from UI option keys to readable labels.
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
    """Build a transport-friendly surveillance configuration from UI inputs.

    The returned dict is intentionally simple so pages can pass it directly to
    `run_live_challenge(...)` without knowing how the live runtime will finally
    interpret the configuration.

    When `mails` is provided, the function also resolves the final runtime
    phrases and returns `phrases` plus `phrase_count`.

    Used by:
    - `src/ui/pages/1_Single_Run.py`
    - `src/ui/pages/2_Multi_Manual_Run.py`
    - `src/ui/pages/3_Multi_Auto_Run.py`
    """
    # This function does not yet decide what the final runtime rule is.
    # It simply captures what the user selected in the UI in a compact and
    # serializable form.
    normalized_method = str(randomization_method).strip().lower()
    if normalized_method not in SURVEILLANCE_RANDOMIZATION_OPTIONS:
        raise ValueError(f"Unsupported surveillance randomization method: {randomization_method}")

    relative_size = float(randomization_relative_size)
    if not 0.0 <= relative_size <= 1.0:
        raise ValueError("Surveillance randomization size must be between 0.0 and 1.0.")

    base_config = {
        "randomization_method": normalized_method,  # Selected helper from `src/ui/engine/randomization.py` for random phrase generation.
        "randomization_relative_size": relative_size,  # Fraction of available phrases to sample in random mode.
        "check_fields": normalize_check_fields(manual_check_fields),  # Which outgoing mail fields should be inspected.
        "phrases_file": manual_phrases_file.strip(),  # Optional JSON file path with reusable phrases.
        "inline_phrases": manual_inline_phrases,  # Optional raw text entered directly in the UI.
    }

    if mails is None:
        return base_config

    file_phrases = load_phrases_from_file(base_config["phrases_file"])
    inline_phrases = parse_inline_phrases(base_config["inline_phrases"])
    generated_phrases = (
        []
        if normalized_method == "none"
        else _build_randomized_phrases(mails=mails, method=normalized_method, relative_size=relative_size)
    )
    phrases = unique_non_empty([*file_phrases, *inline_phrases, *generated_phrases])

    return {
        **base_config,
        "phrases": phrases,
        "phrase_count": len(phrases),
    }


def normalize_check_fields(check_fields: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Normalize UI/runtime check-field settings to a deduplicated field list.

    Accepted forms:
    - `"recipient"`
    - `"subject"`
    - `"both"`
    - `["recipient", "subject"]`

    Internally we always work with a normalized list so
    `src/agent.py::ChallengeEnv` can loop over fields without special-casing
    string variants.
    """
    # `None` means "use the default surveillance behavior".
    if check_fields is None:
        return ["recipient"]

    # UI code may pass a single string or an already built list.
    # We normalize both forms to the same list representation.
    if isinstance(check_fields, str):
        value = check_fields.strip().lower()
        if not value:
            return []
        # `both` is a user-facing convenience value that expands to the two
        # actual runtime fields we know how to inspect.
        if value == "both":
            return ["recipient", "subject"]
        raw_fields = [value]
    else:
        raw_fields = [str(field).strip().lower() for field in check_fields if str(field).strip()]

    fields: list[str] = []
    for field in raw_fields:
        # We validate here so invalid field names fail early, before the runtime
        # has already started a live model call.
        if field not in SURVEILLANCE_FIELD_OPTIONS:
            raise ValueError(f"Unsupported surveillance field: {field}")
        # Preserve order while removing duplicates so later code can just loop.
        if field not in fields:
            fields.append(field)
    return fields


def should_scan_mail(*, mail: dict[str, Any], check_fields: list[str], phrases: list[str]) -> tuple[bool, str | None, str | None]:
    """Return whether a mail should be scanned and which field/phrase matched.

    The decision stays in the surveillance module so `ChallengeEnv` does not
    reimplement any surveillance-specific matching rules.

    Used by `src/agent.py::ChallengeEnv.send_email(...)`.
    """
    for field in check_fields:
        object_to_check = str(mail.get(field, ""))
        for phrase in phrases:
            if phrase.lower() in object_to_check.lower():
                return True, field, phrase
    return False, None, None
