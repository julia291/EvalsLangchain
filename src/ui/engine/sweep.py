"""Utilities for parsing sweep inputs and building execution plans.

This module is used by the UI batch pages to:
1) Parse human-friendly integer specs (for example ``"6,9,12"`` or ``"4-12:2"``),
2) Normalize them into validated integer lists, and
3) Build a cartesian sweep plan for ``target_injections`` x ``max_flags``.

Design goals:
- Keep user input flexible (single values, ranges, mixed forms).
- Fail early with actionable validation errors for invalid specs.
- Preserve input order while removing duplicates.
"""

from __future__ import annotations

from itertools import product


def parse_int_spec(raw: str, *, minimum: int, label: str) -> list[int]:
    """Parse a comma-separated integer specification into a unique ordered list.

    Used by:
    - ``src/ui/pages/3_Multi_Auto_Run.py`` (user input parsing for sweep dimensions)
    - ``src/ui/run_engine.py`` (re-export as stable facade API)

    The parser accepts a compact DSL with three token types:
    - Single values: ``6,9,12``
    - Closed ranges: ``4-10`` (inclusive bounds)
    - Closed ranges with step: ``4-12:2`` (inclusive bounds, step >= 1)

    Mixed forms are allowed, for example: ``3,5-8,10-20:2``.

    Parsing behavior:
    - Values are validated against ``minimum``.
    - Duplicate values are removed.
    - First-seen order is preserved (stable de-duplication).
    - Empty chunks caused by extra commas are ignored.

    Args:
        raw: Raw user input string to parse.
        minimum: Minimum allowed value (inclusive) for every parsed integer.
        label: Field label used in error messages (for user-facing context).

    Returns:
        A non-empty list of integers in first-seen order.

    Raises:
        ValueError: If input is empty, malformed, contains non-integers,
            has invalid ranges/steps, or violates the minimum constraint.

    Examples:
        ``parse_int_spec("6,9,12", minimum=0, label="Target")`` -> ``[6, 9, 12]``
        ``parse_int_spec("4-8:2", minimum=1, label="Flags")`` -> ``[4, 6, 8]``
        ``parse_int_spec("3,3,2-4", minimum=0, label="X")`` -> ``[3, 2, 4]``
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
                start = int(bounds[0])
                end = int(bounds[1])
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
    return values


def build_sweep_plan(
    target_values: list[int],
    max_flag_values: list[int],
    runs_per_combination: int,
) -> tuple[list[tuple[int, int]], int, list[dict[str, int]]]:
    """Build the full parameter sweep matrix and UI preview metadata.

    Used by:
    - ``src/ui/pages/3_Multi_Auto_Run.py`` (build combinations + preview table)
    - ``src/ui/run_engine.py`` (re-export as stable facade API)

    The sweep is the cartesian product of:
    - ``target_values`` (x-axis), and
    - ``max_flag_values`` (y-axis).

    For each combination, ``runs_per_combination`` indicates how many repeated
    executions the caller plans to run (for example to observe stochastic
    variance in live runs).

    Args:
        target_values: Candidate values for ``target_injections``.
        max_flag_values: Candidate values for ``max_flags``.
        runs_per_combination: Planned repeat count per combination.

    Returns:
        A tuple of:
        - combinations: List of ``(target_injections, max_flags)`` tuples.
        - total_runs: ``len(combinations) * runs_per_combination``.
        - preview_rows: Row dicts used directly by UI preview tables. Each row
          includes ``target_injections``, ``max_flags``,
          ``runs_per_combination``, and ``total_planned_runs``.

    Notes:
    - This helper assumes inputs are already validated.
    - It does not enforce positivity of ``runs_per_combination``.
      Validation should happen at the UI/input layer.
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
    return combinations, total_runs, preview_rows
