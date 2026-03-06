"""Multi-run batch page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

try:
    from src.ui.run_engine import (
        DEFAULT_DATASET,
        build_default_system_prompt_template,
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
        build_default_system_prompt_template,
        render_system_prompt,
        run_live_challenge,
        simulate_run,
    )
    from run_store import append_run

st.title("Multi Run")
st.sidebar.header("Multi Run")
st.caption("Define multiple runs and execute them in one batch.")

execution_mode = st.radio(
    "Execution mode",
    options=["simulation", "live_challenge"],
    horizontal=True,
    format_func=lambda x: "Simulation (offline)" if x == "simulation" else "Live Challenge (LLM)",
)

if "multi_count" not in st.session_state:
    st.session_state.multi_count = 3

left, right = st.columns([1, 4])
with left:
    st.session_state.multi_count = st.number_input(
        "Number of runs", min_value=1, max_value=20, step=1, value=st.session_state.multi_count
    )
with right:
    st.info("Set global parameters once. Then tune each run separately below.")

st.subheader("Global parameters")
g_col1, g_col2 = st.columns(2)
with g_col1:
    dataset_path = st.text_input("Dataset path", value=DEFAULT_DATASET, key="multi_dataset")
with g_col2:
    keyword = st.text_input("Keyword", value="boredom", key="multi_keyword")

model_name = st.text_input("Model", value="gemini-2.5-flash", key="multi_model")

api_key = ""
max_emails_value = 0
system_prompt_template = ""
if execution_mode == "live_challenge":
    st.warning("Live mode can be expensive because each run may call the model many times.")
    api_key = st.text_input("API key", type="password", key="multi_api_key")
    max_emails_value = st.number_input(
        "Max emails per run (0 = all)", min_value=0, value=0, step=1, key="multi_max_emails"
    )
    default_prompt_template = build_default_system_prompt_template()
    system_prompt_template = st.text_area(
        "System prompt template (live mode)",
        value=default_prompt_template,
        height=220,
        key="multi_system_prompt",
    )
    st.caption(
        "Note: The template should include {keyword}, {target_injections}, and {max_flags}"
        " so each configuration renders the correct values."
    )

st.subheader("Run configurations")
run_configs: list[dict] = []
for i in range(int(st.session_state.multi_count)):
    with st.expander(f"Run {i + 1}", expanded=i < 2):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            run_name = st.text_input("Name", value=f"multi-run-{i + 1}", key=f"name_{i}")
        with c2:
            target_injections = st.number_input("Target", min_value=0, value=9, step=1, key=f"target_{i}")
        with c3:
            max_flags = st.number_input("Max flags", min_value=1, value=8, step=1, key=f"flags_{i}")
        with c4:
            # `internal_first` is intentionally not available in this branch.
            # Batch strategies must stay independent of recipient categorization.
            strategy = st.selectbox("Strategy (simulation)", options=["early", "random"], key=f"strategy_{i}")

        seed = st.number_input("Seed", min_value=0, value=42 + i, step=1, key=f"seed_{i}")
        notes = st.text_input("Note", value="", key=f"notes_{i}")

        run_configs.append(
            {
                "run_name": run_name,
                "target_injections": int(target_injections),
                "max_flags": int(max_flags),
                "strategy": strategy,
                "seed": int(seed),
                "notes": notes,
            }
        )

if st.button("Start all runs", type="primary"):
    if execution_mode == "live_challenge" and not api_key:
        st.error("API key is required in live challenge mode.")
    else:
        created = []
        progress = st.progress(0)
        status = st.empty()

        for idx, cfg in enumerate(run_configs, start=1):
            status.info(f"Running {cfg['run_name']} ({idx}/{len(run_configs)})...")
            try:
                if execution_mode == "simulation":
                    # Simulation batch path: local deterministic execution, useful for
                    # rapid parameter-combination checks without external model calls.
                    run = simulate_run(
                        run_name=cfg["run_name"],
                        dataset_path=dataset_path,
                        keyword=keyword,
                        target_injections=cfg["target_injections"],
                        max_flags=cfg["max_flags"],
                        strategy=cfg["strategy"],
                        seed=cfg["seed"],
                        model_name=model_name,
                        notes=cfg["notes"],
                    )
                else:
                    # Live batch path: each run invokes the full challenge runtime.
                    # Runs are still persisted in canonical schema for direct comparison.
                    run_prompt = render_system_prompt(
                        prompt_template=system_prompt_template,
                        keyword=keyword,
                        target_injections=cfg["target_injections"],
                        max_flags=cfg["max_flags"],
                    )
                    run = run_live_challenge(
                        run_name=cfg["run_name"],
                        dataset_path=dataset_path,
                        keyword=keyword,
                        target_injections=cfg["target_injections"],
                        max_flags=cfg["max_flags"],
                        model_name=model_name,
                        api_key=api_key,
                        system_prompt=run_prompt,
                        max_emails=None if int(max_emails_value) == 0 else int(max_emails_value),
                        notes=cfg["notes"],
                    )

                append_run(run)
                created.append(run)
            except Exception as exc:
                st.error(f"Error in {cfg['run_name']}: {exc}")

            progress.progress(idx / len(run_configs))

        status.success("Batch finished.")

        if created:
            st.success(f"{len(created)} runs saved successfully.")
            overview = [
                {
                    "run_id": r["run_id"],
                    "name": r["name"],
                    "mode": r.get("parameters", {}).get("execution_mode", r.get("source", "n/a")),
                    "processed": r["summary"]["processed_mails"],
                    "injections": r["summary"]["actual_injections"],
                    "flags": r["summary"]["flagged_count"],
                    "flag_rate": r["summary"]["flag_rate"],
                    "success": r["summary"]["success"],
                }
                for r in created
            ]
            st.dataframe(overview, use_container_width=True)
