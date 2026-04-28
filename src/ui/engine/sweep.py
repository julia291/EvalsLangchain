"""Parameter sweep: parse integer specs and build cartesian execution plans."""

from __future__ import annotations

import logging
from itertools import product

logger = logging.getLogger(__name__)


def parse_int_spec(raw: str, *, minimum: int, label: str) -> list[int]:
    """Parse a comma-separated integer spec into a unique ordered list.

    Supports:
    - Single values: ``6,9,12``
    - Closed ranges: ``4-10``
    - Ranges with step: ``4-12:2``
    - Mixed: ``3,5-8,10-20:2``

    Raises ValueError for empty input, invalid syntax, or values below `minimum`.
    """
    values: list[int] = []
    seen: set[int] = set()
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ValueError(f"{label} must not be empty.")

    for part in parts:
        if "-" in part:
            range_part = part
            step = 1
            if ":" in part:
                range_part, step_part = part.split(":", maxsplit=1)
                try:
                    step = int(step_part.strip())
                except ValueError as exc:
                    raise ValueError(f"{label}: invalid step '{step_part.strip()}'.") from exc
                if step <= 0:
                    raise ValueError(f"{label}: step must be >= 1.")

            bounds = [x.strip() for x in range_part.split("-", maxsplit=1)]
            if len(bounds) != 2 or not bounds[0] or not bounds[1]:
                raise ValueError(f"{label}: invalid range '{part}'.")

            try:
                start, end = int(bounds[0]), int(bounds[1])
            except ValueError as exc:
                raise ValueError(f"{label}: invalid range '{part}'.") from exc

            if start > end:
                raise ValueError(f"{label}: range start must be <= end in '{part}'.")

            for value in range(start, end + 1, step):
                if value < minimum:
                    raise ValueError(f"{label}: value {value} is below minimum {minimum}.")
                if value not in seen:
                    seen.add(value)
                    values.append(value)
            continue

        try:
            value = int(part)
        except ValueError as exc:
            raise ValueError(f"{label}: invalid value '{part}'.") from exc

        if value < minimum:
            raise ValueError(f"{label}: value {value} is below minimum {minimum}.")
        if value not in seen:
            seen.add(value)
            values.append(value)

    if not values:
        raise ValueError(f"{label} must contain at least one value.")

    logger.debug("Parsed spec '%s' for '%s': %d values", raw, label, len(values))
    return values


def build_sweep_plan(
    target_values: list[int],
    max_flag_values: list[int],
    runs_per_combination: int,
) -> tuple[list[tuple[int, int]], int, list[dict[str, int]]]:
    """Build the cartesian parameter matrix for a batch sweep.

    Returns (combinations, total_runs, preview_rows).
    `combinations` is the list of (target_injections, max_flags) tuples.
    `preview_rows` can be passed directly to st.dataframe.
    """
    combinations = list(product(target_values, max_flag_values))
    total_runs = len(combinations) * int(runs_per_combination)
    preview_rows = [
        {
            "target_injections": target,
            "max_flags": max_flags,
            "runs_per_combination": int(runs_per_combination),
            "total_planned_runs": int(total_runs),
        }
        for target, max_flags in combinations
    ]

    logger.info("Sweep plan: %d combinations x %d reps = %d total runs",
                len(combinations), runs_per_combination, total_runs)
    return combinations, total_runs, preview_rows
