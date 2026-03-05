"""Results page for run inspection and comparison.

This page now connects to:
- newly executed UI runs (simulation/live)
- legacy repository result files (import into canonical run format)
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Import with fallback so this page works even if package path differs per launch.
try:
    from src.ui.run_engine import import_legacy_results_file
    from src.ui.run_store import append_run, load_runs
except ModuleNotFoundError:
    ui_dir = Path(__file__).resolve().parents[1]
    if str(ui_dir) not in sys.path:
        sys.path.insert(0, str(ui_dir))

    from run_engine import import_legacy_results_file
    from run_store import append_run, load_runs

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

# Page framing.
st.title("Results")
st.sidebar.header("Results")
st.caption("Visualize and compare simulated, live, and imported runs.")

# Load persisted run history.
runs = load_runs()

if not runs:
    st.warning("No UI runs found yet. Start a single or multi run first.")
else:
    # Most recent runs first.
    runs_sorted = sorted(runs, key=lambda r: r.get("created_at", ""), reverse=True)
    options = [f"{r['name']} ({r['run_id']})" for r in runs_sorted]

    # User selects a run for deep inspection.
    selected_label = st.selectbox("Select run", options=options)
    selected_idx = options.index(selected_label)
    selected_run = runs_sorted[selected_idx]

    summary = selected_run["summary"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Processed", summary["processed_mails"])
    c2.metric("Injections", f"{summary['actual_injections']} / {summary['target_injections']}")
    c3.metric("Flags", f"{summary['flagged_count']} / {summary['max_flags']}")
    c4.metric("Flag rate", f"{summary['flag_rate']}%")
    c5.metric("Mode", selected_run.get("parameters", {}).get("execution_mode", selected_run.get("source", "n/a")))

    # Parameter payload clarifies how the run was configured.
    st.subheader("Run parameters")
    st.json(selected_run["parameters"])

    # Show normalized per-mail records.
    st.subheader("Mail results")
    st.dataframe(selected_run["results"], use_container_width=True)

    # Live challenge runs include extra audit trail for debugging model behavior.
    if selected_run.get("audit_log"):
        st.subheader("Audit log")
        st.dataframe(selected_run["audit_log"], use_container_width=True)

    st.subheader("Run comparison")
    comp_rows = [
        {
            "name": r["name"],
            "run_id": r["run_id"],
            "mode": r.get("parameters", {}).get("execution_mode", r.get("source", "n/a")),
            "processed": r["summary"]["processed_mails"],
            "injections": r["summary"]["actual_injections"],
            "flags": r["summary"]["flagged_count"],
            "flag_rate": r["summary"]["flag_rate"],
            "success": r["summary"]["success"],
        }
        for r in runs_sorted
    ]

    if pd is not None:
        df = pd.DataFrame(comp_rows)
        st.dataframe(df, use_container_width=True)

        # Keep chart simple and comparable across run modes.
        st.bar_chart(df.set_index("name")[["injections", "flags"]])
    else:
        st.dataframe(comp_rows, use_container_width=True)

st.divider()
st.subheader("Import legacy repository results")

# Legacy files shipped with repository that users may want in the dashboard timeline.
repo_root = Path(__file__).resolve().parents[3]
candidate_files = [
    repo_root / "data" / "results.json",
    repo_root / "data" / "results_no_a.json",
]
existing = [p for p in candidate_files if p.exists()]

if not existing:
    st.info("No bundled legacy result files found in data/.")
else:
    selected_file = st.selectbox("Legacy file", options=[str(p) for p in existing])
    import_run_name = st.text_input("Imported run name", value=f"import-{Path(selected_file).stem}")
    import_keyword = st.text_input("Keyword for import analysis", value="boredom")
    import_target = st.number_input("Target injections for import", min_value=0, value=0, step=1)
    import_max_flags = st.number_input("Max flags for import", min_value=1, value=8, step=1)

    col_preview, col_import = st.columns(2)

    with col_preview:
        if st.button("Preview file"):
            try:
                run = import_legacy_results_file(
                    results_path=selected_file,
                    run_name=import_run_name,
                    keyword=import_keyword,
                    target_injections=int(import_target),
                    max_flags=int(import_max_flags),
                )
                st.dataframe(run["results"], use_container_width=True)
            except Exception as exc:
                st.error(f"Could not preview file: {exc}")

    with col_import:
        if st.button("Import file as run"):
            try:
                run = import_legacy_results_file(
                    results_path=selected_file,
                    run_name=import_run_name,
                    keyword=import_keyword,
                    target_injections=int(import_target),
                    max_flags=int(import_max_flags),
                )
                append_run(run)
                st.success(f"Imported run saved: {run['name']} ({run['run_id']})")
            except Exception as exc:
                st.error(f"Could not import file: {exc}")
