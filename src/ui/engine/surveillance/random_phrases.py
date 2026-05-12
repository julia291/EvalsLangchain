"""Recipient-derived random phrase samplers.

The Multiple Runs page lets the user generate a randomized phrase list
from the dataset's recipient addresses, instead of (or in addition to)
typing phrases manually. This module owns those samplers.

Each sampler takes the full mail list and a ``relative_size`` between 0
and 1, and returns a random subset (without replacement) of phrases of
the requested flavor — full address, local part, domain, or TLD. Mails
without a usable ``recipient`` are skipped silently so a malformed entry
does not crash the run.
"""

from __future__ import annotations

import logging
import random
from math import ceil
from typing import Any, Callable

from .phrase_sources import deduplicate_phrase_values

logger = logging.getLogger(__name__)


def load_random_phrase_methods() -> dict[str, Callable[[list[dict[str, Any]], float], list[str]]]:
    """Return the available recipient-based randomization helpers.

    Keys match the ``randomization_method`` values accepted by the
    surveillance settings builder.
    """
    return {
        "whole_recipient": sample_recipient_addresses,
        "recipient_name": sample_recipient_local_parts,
        "recipient_domain": sample_recipient_domains,
        "recipient_tld": sample_recipient_tlds,
    }


def build_randomized_phrase_sample(
    *,
    mails: list[dict[str, Any]],
    method: str,
    relative_size: float,
) -> list[str]:
    """Build phrases via one of the predefined randomization helpers."""
    methods = load_random_phrase_methods()
    if method not in methods:
        raise ValueError(f"Unsupported surveillance randomization method: {method}")

    phrases = methods[method](mails, relative_size)
    return deduplicate_phrase_values(phrases)


def _recipients(mails: list[dict[str, Any]]) -> list[str]:
    """Return non-empty lowercased recipient addresses from ``mails``.

    Defensive fallback: this code path is meant to run after pre-flight
    validation has already rejected datasets with missing recipients
    (see ``src/ui/engine/preflight.py``). If a bad row still reaches the
    sampler, it is dropped from the phrase pool and a warning is logged
    so the issue surfaces instead of silently biasing the sample.
    """
    recipients: list[str] = []
    for mail in mails:
        value = mail.get("recipient")
        if not value:
            logger.warning(
                "Mail id=%r has no recipient; skipping in surveillance sampling.",
                mail.get("id"),
            )
            continue
        recipients.append(str(value).lower())
    return recipients


def _sample(flags: set[str], rel_size: float) -> list[str]:
    """Return a random subset of ``flags`` sized by ``rel_size``."""
    if not flags:
        return []
    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def sample_recipient_addresses(mails: list[dict[str, Any]], rel_size: float) -> list[str]:
    """Randomly select whole recipient addresses to use as flags."""
    return _sample(set(_recipients(mails)), rel_size)


def sample_recipient_local_parts(mails: list[dict[str, Any]], rel_size: float) -> list[str]:
    """Randomly select recipient local parts (before ``@``) to use as flags."""
    flags: set[str] = set()
    for recipient in _recipients(mails):
        local_part = recipient.split("@", 1)[0]
        if local_part:
            flags.add(local_part)
    return _sample(flags, rel_size)


def sample_recipient_domains(mails: list[dict[str, Any]], rel_size: float) -> list[str]:
    """Randomly select recipient domains (after ``@``) to use as flags."""
    flags: set[str] = set()
    for recipient in _recipients(mails):
        if "@" not in recipient:
            continue
        domain = recipient.split("@", 1)[1]
        if domain:
            flags.add(domain)
    return _sample(flags, rel_size)


def sample_recipient_tlds(mails: list[dict[str, Any]], rel_size: float) -> list[str]:
    """Randomly select recipient top-level domains to use as flags."""
    flags: set[str] = set()
    for recipient in _recipients(mails):
        if "@" not in recipient:
            continue
        domain = recipient.split("@", 1)[1]
        if "." not in domain:
            continue
        tld = domain.rsplit(".", 1)[-1]
        if tld:
            flags.add(tld)
    return _sample(flags, rel_size)
