"""Simulation execution helpers."""

from __future__ import annotations

import random
from typing import Any

from .loaders import load_mails, mail_text, recipient
from .record_builder import build_run_record


def injection_order(mails: list[dict[str, Any]], strategy: str, seed: int) -> list[int]:
    """Return index order for selecting keyword injections.

    Used by:
    - `simulate_run` in this file

    Supported strategies:
    - `early`
    - `random`
    """
    indices = list(range(len(mails)))
    if strategy == "random":
        rng = random.Random(seed)
        rng.shuffle(indices)
    return indices


def simulate_run(
    run_name: str,
    dataset_path: str,
    keyword: str,
    target_injections: int,
    max_flags: int,
    strategy: str = "unchanged",
    seed: int = 42,
    model_name: str = "gemini-2.5-flash",
    notes: str = "",
) -> dict[str, Any]:
    """Execute deterministic simulation mode.

    Simulation is retained for tests and legacy experiments, but it is not
    exposed in the simplified Streamlit navigation.
    """
    mails = load_mails(dataset_path)
    order = injection_order(mails, strategy=strategy, seed=seed)
    selected = set(order[: max(0, target_injections)])

    rows: list[dict[str, Any]] = []
    flagged_count = 0

    for idx, mail in enumerate(mails):
        base_text = mail_text(mail)
        keyword_inserted = idx in selected

        content = base_text
        if keyword_inserted:
            content = f"{base_text}\n\n{keyword}"

        flagged = keyword_inserted
        if flagged:
            flagged_count += 1

        rows.append(
            {
                "id": mail.get("id", idx + 1),
                "recipient": recipient(mail),
                "subject": mail.get("subject", ""),
                "content": content,
                "keyword_inserted": keyword_inserted,
                "flagged": flagged,
            }
        )

        if flagged_count >= max_flags:
            break

    parameters = {
        "execution_mode": "simulation",
        "dataset_path": dataset_path,
        "keyword": keyword,
        "target_injections": target_injections,
        "max_flags": max_flags,
        "strategy": strategy,
        "seed": seed,
        "model_name": model_name,
        "notes": notes,
    }

    return build_run_record(
        run_name=run_name,
        parameters=parameters,
        rows=rows,
        total_mails=len(mails),
        source="simulation",
    )
