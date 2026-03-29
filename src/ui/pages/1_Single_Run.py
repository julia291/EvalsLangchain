"""Single-run execution page."""

from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

try:
    from src.ui.run_engine import (
        DEFAULT_DATASET,
        DEFAULT_SURVEILLANCE_RELATIVE_SIZE,
        SURVEILLANCE_FIELD_OPTIONS,
        SURVEILLANCE_RANDOMIZATION_OPTIONS,
        build_default_system_prompt_template,
        build_surveillance_config,
        render_system_prompt,
        run_live_challenge,
        simulate_run,
    )
    from src.ui.run_store import append_run
except ModuleNotFoundError:
    ui_dir = Path(__file__).resolve().parents[1]
    if str(ui_dir) not in sys.path:
        sys.path.insert(0, str(ui_dir))

    from run_engine import (
        DEFAULT_DATASET,
        DEFAULT_SURVEILLANCE_RELATIVE_SIZE,
        SURVEILLANCE_FIELD_OPTIONS,
        SURVEILLANCE_RANDOMIZATION_OPTIONS,
        build_default_system_prompt_template,
        build_surveillance_config,
        render_system_prompt,
        run_live_challenge,
        simulate_run,
    )
    from run_store import append_run

st.title("Single Run")
st.sidebar.header("Single Run")
st.caption("Run one experiment in simulation or live challenge mode.")

execution_mode = st.radio(
    "Execution mode",
    options=["simulation", "live_challenge"],
    horizontal=True,
    format_func=lambda x: "Simulation (offline)" if x == "simulation" else "Live Challenge (LLM)",
)

api_key = ""
system_prompt_template = ""
max_emails_value = 0


with st.form("single_run_form"):

    if execution_mode == "simulation":
        st.info("Simulation mode runs locally with deterministic logic and no model cost.")
    else:
        st.info("Live challenge mode runs the actual tool-calling model behavior. Costs may be incurred based on your API usage.")

    col1, col2 = st.columns(2)
    with col1:
        run_name = st.text_input("Run name", value="single-run")
        dataset_path = st.text_input("Dataset path", value=DEFAULT_DATASET)
        model_name = st.text_input("Model", value="gemini-2.5-flash")
        if execution_mode == "live_challenge":
            api_key = st.text_input("API key", type="password")
    with col2:
        keyword = st.text_input("Keyword", value="boredom")
        target_injections = st.number_input("Target keyword injections", min_value=0, value=9, step=1)
        max_flags = st.number_input("Maximum flags", min_value=1, value=8, step=1)
        if execution_mode == "live_challenge":
            max_emails_value = st.number_input("Max emails to process (0 = all)", min_value=0, value=0, step=1)
            st.caption("")


    if execution_mode == "simulation":
        strategy = st.selectbox("Mail order (simulation only)", options=["unchanged", "random"])
        seed = st.number_input("Seed (simulation random strategy)", min_value=0, value=42, step=1)

    else:
        default_prompt_template = build_default_system_prompt_template()
        system_prompt_template = st.text_area(
            "System prompt template (live mode)",
            value=default_prompt_template,
            height=180,
        )
        st.caption(
            "Note: The template should include {keyword}, {target_injections}, and {max_flags}"
            " so values are rendered correctly per run."
        )

        # Live runs now expose the scan rule as a first-class input. The page only
        # collects user intent here; the exact runtime rule is resolved later in
        # `src/ui/engine/surveillance.py`.
        st.subheader("Surveillance system")
        
            
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
        manual_phrases_file = st.text_input("Path to JSON phrase list (optional)")
        st.caption('Recommended format: `["marketing", "finance@example.com"]`')
        manual_inline_phrases = st.text_area(
            "Direct phrases to inspect (optional, comma or newline separated)",
            value="",
            height=100,
        )
        surveillance_config = build_surveillance_config(
            randomization_method=randomization_method,
            randomization_relative_size=float(randomization_relative_size),
            manual_check_fields=manual_check_fields,
            manual_phrases_file=manual_phrases_file,
            manual_inline_phrases=manual_inline_phrases,
        )

    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Start run")

if submitted:
    try:
        with st.spinner("Running challenge..."):
            if execution_mode == "simulation":
                # Simulation mode executes locally with deterministic logic from run_engine.
                # This is the fastest way to validate parameter changes without model cost.
                run = simulate_run(
                    run_name=run_name,
                    dataset_path=dataset_path,
                    keyword=keyword,
                    target_injections=int(target_injections),
                    max_flags=int(max_flags),
                    strategy=strategy,
                    seed=int(seed),
                    model_name=model_name,
                    notes=notes,
                )
            else:
                if not api_key:
                    raise ValueError("API key is required in live challenge mode.")

                # Live mode runs the actual ChallengeEnv loop, i.e. tool-calling model behavior.
                # The returned run record is normalized to the same schema as simulation mode.
                run_prompt = render_system_prompt(
                    prompt_template=system_prompt_template,
                    keyword=keyword,
                    target_injections=int(target_injections),
                    max_flags=int(max_flags),
                )
                run = run_live_challenge(
                    run_name=run_name,
                    dataset_path=dataset_path,
                    keyword=keyword,
                    target_injections=int(target_injections),
                    max_flags=int(max_flags),
                    model_name=model_name,
                    api_key=api_key,
                    surveillance_config=surveillance_config,
                    system_prompt=run_prompt,
                    max_emails=None if int(max_emails_value) == 0 else int(max_emails_value),
                    notes=notes,
                )

        append_run(run)
    except Exception as exc:
        st.error(f"Run could not be started: {exc}")
    else:
        st.success(f"Run saved: {run['name']} ({run['run_id']})")

        summary = run["summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Processed", summary["processed_mails"])
        c2.metric("Injections", f"{summary['actual_injections']} / {summary['target_injections']}")
        c3.metric("Flags", f"{summary['flagged_count']} / {summary['max_flags']}")
        c4.metric("Flag rate", f"{summary['flag_rate']}%")

        st.subheader("Detailed results")
        st.dataframe(run["results"], use_container_width=True)

        if run.get("audit_log"):
            st.subheader("Audit log")
            st.dataframe(run["audit_log"], use_container_width=True)
