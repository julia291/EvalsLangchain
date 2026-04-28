"""Recipient-based phrase randomization for the surveillance system."""

from __future__ import annotations

import logging
import random
from math import ceil
from typing import Any, Callable

from .helpers import unique_non_empty

logger = logging.getLogger(__name__)


def _load_randomization_methods() -> dict[str, Callable[[list[dict[str, Any]], float], list[str]]]:
    return {
        "whole_recipient": random_whole_flags,
        "recipient_name": random_name_flags,
        "recipient_domain": random_domain_flags,
        "recipient_tld": random_tld_flags,
    }


def _build_randomized_phrases(*, mails: list[dict[str, Any]], method: str, relative_size: float) -> list[str]:
    """Sample phrases from mail data using the given method and relative size."""
    methods = _load_randomization_methods()
    if method not in methods:
        raise ValueError(f"Unsupported surveillance randomization method: {method}")

    phrases = methods[method](mails, relative_size)
    result = unique_non_empty(str(item) for item in phrases)
    logger.debug("Randomized phrases via '%s': %d sampled from %d mails", method, len(result), len(mails))
    return result


def random_whole_flags(mails: list[dict], rel_size: float) -> list:
    """Sample full recipient addresses."""
    flags = {mail.get("recipient").lower() for mail in mails}
    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def random_name_flags(mails: list[dict], rel_size: float) -> list:
    """Sample local parts (before @) of recipient addresses."""
    flags = {mail.get("recipient").split("@", 1)[0].lower() for mail in mails}
    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def random_domain_flags(mails: list[dict], rel_size: float) -> list:
    """Sample domains (after @) of recipient addresses."""
    flags = {mail.get("recipient").split("@", 1)[1].lower() for mail in mails}
    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))


def random_tld_flags(mails: list[dict], rel_size: float) -> list:
    """Sample top-level domains of recipient addresses."""
    flags = {mail.get("recipient").split("@", 1)[1].lower().split(".")[-1] for mail in mails}
    subset_size = ceil(rel_size * len(flags))
    return random.sample(list(flags), min(subset_size, len(flags)))
