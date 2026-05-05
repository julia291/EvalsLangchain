"""Automatic live multi-run page."""

from __future__ import annotations

import streamlit as st

from src.ui.engine.config import DEFAULT_DATASET
from src.ui.engine.runs.automatic_batch import build_run_summary_table, run_automatic_live_batch
from src.ui.engine.runs.live_challenge import run_live_challenge_run
from src.ui.engine.runs.live_prompts import build_default_live_prompt_template
from src.ui.engine.runs.parameter_sweep import build_parameter_sweep_plan, parse_integer_sweep_values
from src.ui.engine.surveillance.settings import (
    DEFAULT_SURVEILLANCE_RELATIVE_SIZE,
    SURVEILLANCE_FIELD_OPTIONS,
    SURVEILLANCE_RANDOMIZATION_OPTIONS,
    build_surveillance_settings,
)
from src.ui.store.repository import append_run


st.title("Multiple Runs")
st.sidebar.header("Multiple Runs")
st.caption("Run automatic live sweeps over target-injection and flag-limit combinations.")
st.warning("This page starts live LLM runs only. API usage costs may apply.")

st.subheader("Global settings")
global_left, global_right = st.columns(2)
with global_left:
    run_name_prefix = st.text_input("Run name prefix", value="auto-live")
    dataset_path = st.text_input("Dataset path", value=DEFAULT_DATASET)
    keyword = st.text_input("Keyword", value="boredom")
    model_name = st.text_input("Model", value="gemini-2.5-flash")

with global_right:
    api_key = st.text_input("API key", type="password")
    max_emails_value = st.number_input("Max emails per run (0 = all)", min_value=0, value=0, step=1)
    runs_per_combination = st.number_input("Live runs per combination", min_value=1, value=2, step=1)
    notes = st.text_area("Notes (applied to every run)", value="")

st.subheader("Surveillance system")
surveillance_left, surveillance_right = st.columns(2)
with surveillance_left:
    randomization_method = st.selectbox(
        "Randomization method",
        options=list(SURVEILLANCE_RANDOMIZATION_OPTIONS.keys()),
        format_func=lambda key: SURVEILLANCE_RANDOMIZATION_OPTIONS[key],
    )
    randomization_relative_size = st.slider(
        "Relative sample size",
        min_value=0.0,
        max_value=1.0,
        value=float(DEFAULT_SURVEILLANCE_RELATIVE_SIZE),
        step=0.05,
    )
    manual_check_fields = st.multiselect(
        "Fields to inspect",
        options=SURVEILLANCE_FIELD_OPTIONS,
        default=["recipient"],
    )

with surveillance_right:
    manual_phrases_file = st.text_input("Path to JSON phrase list (optional)")
    st.caption('Recommended format: `["marketing", "finance@example.com"]`')
    manual_inline_phrases = st.text_area(
        "Direct phrases to inspect (optional, comma or newline separated)",
        value="",
        height=100,
    )

surveillance_config = build_surveillance_settings(
    randomization_method=randomization_method,
    randomization_relative_size=float(randomization_relative_size),
    manual_check_fields=manual_check_fields,
    manual_phrases_file=manual_phrases_file,
    manual_inline_phrases=manual_inline_phrases,
)

st.subheader("Parameter combinations")
param_left, param_right = st.columns(2)
with param_left:
    target_spec = st.text_input(
        "Target keyword injections (list/ranges)",
        value="6,9,12",
        help="Examples: 5,8,11 or 4-10 or 4-12:2",
    )
with param_right:
    max_flags_spec = st.text_input(
        "Max flags (list/ranges)",
        value="6,8",
        help="Examples: 5,7,9 or 4-10 or 4-12:2",
    )

st.subheader("Prompt template")
st.caption("Keep {keyword}, {target_injections}, and {max_flags} for per-run rendering.")
system_prompt_template = st.text_area(
    "System prompt template",
    value=build_default_live_prompt_template(),
    height=220,
)

target_values: list[int] = []
max_flag_values: list[int] = []
input_error = ""
try:
    target_values = parse_integer_sweep_values(target_spec, minimum=0, label="Target keyword injections")
    max_flag_values = parse_integer_sweep_values(max_flags_spec, minimum=1, label="Max flags")
except ValueError as exc:
    input_error = str(exc)

if input_error:
    st.error(input_error)
    combinations: list[tuple[int, int]] = []
else:
    combinations, total_runs, preview_rows = build_parameter_sweep_plan(
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


def update_progress(done: int, total: int, run_name: str) -> None:
    status_text.info(f"Running {run_name} ({min(done + 1, total)}/{total})...")
    progress_bar.progress(done / total if total else 0)


start_disabled = bool(input_error) or len(combinations) == 0
if st.button("Start automatic live runs", type="primary", disabled=start_disabled):
    if not api_key:
        st.error("API key is required for live runs.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        batch_result = run_automatic_live_batch(
            run_name_prefix=run_name_prefix,
            combinations=combinations,
            runs_per_combination=int(runs_per_combination),
            dataset_path=dataset_path,
            keyword=keyword,
            model_name=model_name,
            api_key=api_key,
            surveillance_config=surveillance_config,
            system_prompt_template=system_prompt_template,
            max_emails=None if int(max_emails_value) == 0 else int(max_emails_value),
            notes=notes,
            run_live=run_live_challenge_run,
            save_run=append_run,
            progress_callback=update_progress,
        )

        status_text.success("Automatic live batch finished.")
        st.success(f"{len(batch_result.created)} run(s) saved successfully.")

        if batch_result.failures:
            st.error(f"{len(batch_result.failures)} run(s) failed.")
            st.dataframe(batch_result.failure_rows, use_container_width=True)

        if batch_result.created:
            st.dataframe(build_run_summary_table(batch_result.created), use_container_width=True)
