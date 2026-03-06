"""Automatic multi-run page for live LLM parameter combinations.

This page focuses on one concrete workflow:
- Run *live* challenge executions (LLM-backed, not simulation).
- Run all combinations of `target_injections` and `max_flags`.
- Repeat each parameter combination `n` times to observe variance.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Import strategy:
# 1) Normal package imports when app is started from project root.
# 2) Local fallback when Streamlit executes page scripts without package context.
try:
    from src.ui.run_engine import (
        DEFAULT_DATASET,
        build_default_system_prompt_template,
        build_sweep_plan,
        parse_int_spec,
        render_system_prompt,
        run_live_challenge,
    )
    from src.ui.run_store import append_run
except ModuleNotFoundError:
    ui_dir = Path(__file__).resolve().parents[1]
    if str(ui_dir) not in sys.path:
        sys.path.insert(0, str(ui_dir))

    from run_engine import (
        DEFAULT_DATASET,
        build_default_system_prompt_template,
        build_sweep_plan,
        parse_int_spec,
        render_system_prompt,
        run_live_challenge,
    )
    from run_store import append_run


# Build a default template with placeholders for this page.
default_prompt_template = build_default_system_prompt_template()

# --- Page header and high-level intent -----------------------------------------------------------
st.title("Multi Automatic Run")
st.sidebar.header("Multi Automatic Run")
st.caption("Run all parameter combinations automatically in live challenge mode.")

st.warning("This page starts live LLM runs only. API usage costs may apply.")

# --- Global run settings -------------------------------------------------------------------------
# These values are shared by every generated run in the batch.
st.subheader("Global settings")
g_col1, g_col2 = st.columns(2)
    
with g_col1:
    run_name_prefix = st.text_input("Run name prefix", value="auto-live")
    dataset_path = st.text_input("Dataset path", value=DEFAULT_DATASET)
    keyword = st.text_input("Keyword", value="boredom")
    model_name = st.text_input("Model", value="gemini-2.5-flash")

with g_col2:
    api_key = st.text_input("API key", type="password")
    max_emails_value = st.number_input("Max emails per run (0 = all)", min_value=0, value=0, step=1)
    runs_per_combination = st.number_input("Live runs per combination", min_value=1, value=2, step=1)
    notes = st.text_area("Notes (applied to every run)", value="")

# --- Parameter dimensions ------------------------------------------------------------------------
# Users define value sets for both dimensions.
# The cartesian product(target_values, max_flag_values) is executed later.
st.subheader("Parameter combinations")
p_col1, p_col2 = st.columns(2)
with p_col1:
    target_spec = st.text_input(
        "Target keyword injections (list/ranges)",
        value="6,9,12",
        help="Examples: 5,8,11 or 4-10 or 4-12:2",
    )
with p_col2:
    max_flags_spec = st.text_input(
        "Max flags (list/ranges)",
        value="6,8",
        help="Examples: 5,7,9 or 4-10 or 4-12:2",
    )

# --- Prompt template -----------------------------------------------------------------------------
# The prompt can be fully custom but can also be parameterized with placeholders.
st.subheader("Prompt template")
st.caption(
    "The template should include {keyword}, {target_injections}, and {max_flags}"
    " so every parameter combination is rendered correctly."
)
system_prompt_template = st.text_area(
    "System prompt template",
    value=default_prompt_template,
    height=220,
)

# Parse and validate parameter dimensions before showing execution controls.
target_values: list[int] = []
max_flag_values: list[int] = []
input_error = ""
try:
    target_values = parse_int_spec(target_spec, minimum=0, label="Target keyword injections")
    max_flag_values = parse_int_spec(max_flags_spec, minimum=1, label="Max flags")
except ValueError as exc:
    input_error = str(exc)

if input_error:
    # Input validation errors are shown immediately; execution stays disabled.
    st.error(input_error)
    combinations: list[tuple[int, int]] = []
else:
    # Build full parameter matrix and a UI preview from shared helpers.
    combinations, total_runs, preview_rows = build_sweep_plan(
        target_values=target_values,
        max_flag_values=max_flag_values,
        runs_per_combination=int(runs_per_combination),
    )

    st.info(
        "Parameter combinations: "
        f"{len(combinations)} ({len(target_values)} targets x {len(max_flag_values)} max-flags). "
        f"Total live runs: {total_runs}."
    )
    st.dataframe(preview_rows, use_container_width=True)

# Prevent accidental starts when required parameter input is invalid or empty.
start_disabled = bool(input_error) or len(combinations) == 0
if st.button("Start automatic live runs", type="primary", disabled=start_disabled):
    # Hard gate for live mode: key is required before any call.
    if not api_key:
        st.error("API key is required for live runs.")
    else:
        # `created` stores successful canonical run records.
        # `failures` captures non-fatal failures so the remaining batch can continue.
        created: list[dict] = []
        failures: list[dict[str, str]] = []
        total_runs = len(combinations) * int(runs_per_combination)
        progress = st.progress(0)
        status = st.empty()

        run_counter = 0
        for combo_index, (target_injections, max_flags) in enumerate(combinations, start=1):
            # Repeat each parameter combination `n` times.
            for repetition in range(1, int(runs_per_combination) + 1):
                run_counter += 1
                # Run-name schema encodes parameter dimensions for easier filtering later.
                run_name = (
                    f"{run_name_prefix}"
                    f"-t{target_injections}"
                    f"-f{max_flags}"
                    f"-r{repetition}"
                )
                status.info(
                    f"Running {run_name} "
                    f"({run_counter}/{total_runs}, combo {combo_index}/{len(combinations)})..."
                )

                # Persist parameter metadata in notes so results are traceable even if names change.
                run_notes = (
                    f"{notes}\n"
                    f"auto.target_injections={target_injections}\n"
                    f"auto.max_flags={max_flags}\n"
                    f"auto.repetition={repetition}/{int(runs_per_combination)}"
                ).strip()
                run_prompt = render_system_prompt(
                    prompt_template=system_prompt_template,
                    keyword=keyword,
                    target_injections=target_injections,
                    max_flags=max_flags,
                )

                try:
                    # Main live execution path: calls the LLM-powered challenge runtime.
                    run = run_live_challenge(
                        run_name=run_name,
                        dataset_path=dataset_path,
                        keyword=keyword,
                        target_injections=target_injections,
                        max_flags=max_flags,
                        model_name=model_name,
                        api_key=api_key,
                        system_prompt=run_prompt,
                        max_emails=None if int(max_emails_value) == 0 else int(max_emails_value),
                        notes=run_notes,
                    )
                    # Save each successful run immediately (safer than buffering until the end).
                    append_run(run)
                    created.append(run)
                except Exception as exc:
                    # Batch should continue after failures so one bad run does not stop all combinations.
                    failures.append(
                        {
                            "run_name": run_name,
                            "target_injections": str(target_injections),
                            "max_flags": str(max_flags),
                            "repetition": f"{repetition}/{int(runs_per_combination)}",
                            "error": str(exc),
                        }
                    )

                # Update progress after each attempted run (success or failure).
                progress.progress(run_counter / total_runs)

        status.success("Automatic live batch finished.")
        st.success(f"{len(created)} run(s) saved successfully.")

        if failures:
            # Expose failures transparently for retry/debugging.
            st.error(f"{len(failures)} run(s) failed.")
            st.dataframe(failures, use_container_width=True)

        if created:
            # Compact summary table for quick comparison across generated runs.
            overview = [
                {
                    "run_id": run["run_id"],
                    "name": run["name"],
                    "target_injections": run.get("parameters", {}).get("target_injections"),
                    "max_flags": run.get("parameters", {}).get("max_flags"),
                    "processed": run["summary"]["processed_mails"],
                    "injections": run["summary"]["actual_injections"],
                    "flags": run["summary"]["flagged_count"],
                    "flag_rate": run["summary"]["flag_rate"],
                    "success": run["summary"]["success"],
                }
                for run in created
            ]
            st.dataframe(overview, use_container_width=True)
