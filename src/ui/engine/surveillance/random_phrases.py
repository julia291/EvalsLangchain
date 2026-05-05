from __future__ import annotations

import random
from math import ceil
from typing import Any, Callable

from .phrase_sources import deduplicate_phrase_values


def load_random_phrase_methods() -> dict[str, Callable[[list[dict[str, Any]], float], list[str]]]:
    """Return the available recipient-based randomization helpers."""
    return {
        "whole_recipient": sample_recipient_addresses,
        "recipient_name": sample_recipient_local_parts,
        "recipient_domain": sample_recipient_domains,
        "recipient_tld": sample_recipient_tlds,
    }


def build_randomized_phrase_sample(*, mails: list[dict[str, Any]], method: str, relative_size: float) -> list[str]:
    """Build phrases via one of the predefined randomization helpers."""
    methods = load_random_phrase_methods()
    if method not in methods:
        raise ValueError(f"Unsupported surveillance randomization method: {method}")

    phrases = methods[method](mails, relative_size)
    return deduplicate_phrase_values(str(item) for item in phrases)


def sample_recipient_addresses(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects a whole recipient from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flags.add(mail.get("recipient").lower())

    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def sample_recipient_local_parts(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects names from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flag = mail.get("recipient").split("@", 1)[0].lower()
        flags.add(flag)

    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def sample_recipient_domains(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flag = mail.get("recipient").split("@", 1)[1].lower()
        flags.add(flag)

    subset_size = ceil(rel_size * len(flags))

    return random.sample(list(flags), min(subset_size, len(flags)))


def sample_recipient_tlds(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects top-level domains from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flag = mail.get("recipient").split("@", 1)[1].lower().split(".")[-1]
        flags.add(flag)

    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))
