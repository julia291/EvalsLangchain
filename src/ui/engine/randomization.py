from __future__ import annotations

import random
from math import ceil
from typing import Any, Callable

from .helpers import unique_non_empty


def _load_randomization_methods() -> dict[str, Callable[[list[dict[str, Any]], float], list[str]]]:
    """Return the available recipient-based randomization helpers."""
    return {
        "whole_recipient": random_whole_flags,
        "recipient_name": random_name_flags,
        "recipient_domain": random_domain_flags,
        "recipient_tld": random_tld_flags,
    }


def _build_randomized_phrases(*, mails: list[dict[str, Any]], method: str, relative_size: float) -> list[str]:
    """Build phrases via one of the predefined randomization helpers."""
    methods = _load_randomization_methods()
    if method not in methods:
        raise ValueError(f"Unsupported surveillance randomization method: {method}")

    phrases = methods[method](mails, relative_size)
    return unique_non_empty(str(item) for item in phrases)


def random_whole_flags(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects a whole recipient from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flags.add(mail.get("recipient").lower())

    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def random_name_flags(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects names from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flag = mail.get("recipient").split("@", 1)[0].lower()
        flags.add(flag)

    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def random_domain_flags(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects domains from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flag = mail.get("recipient").split("@", 1)[1].lower()
        flags.add(flag)

    subset_size = ceil(rel_size * len(flags))

    return random.sample(list(flags), min(subset_size, len(flags)))


def random_tld_flags(mails: list[dict], rel_size: float) -> list:
    """
    Randomly selects top-level domains from the emails to be used as flags.
    """

    flags = set()

    for mail in mails:
        flag = mail.get("recipient").split("@", 1)[1].lower().split(".")[-1]
        flags.add(flag)

    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))
