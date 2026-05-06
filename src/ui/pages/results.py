"""Results page for live run inspection and comparison."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import streamlit as st

repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.ui.store.repository import load_runs

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


def display_value(value: Any) -> Any:
    """Return dataframe-friendly values for nested hyperparameters."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


st.title("Results")
st.sidebar.header("Results")
st.caption("Visualize and compare saved live runs.")

runs = sorted(load_runs(), key=lambda r: r.get("created_at", ""), reverse=True)

if not runs:
    st.warning("No UI runs found yet. Start an automatic live batch first.")
else:
    labels = [f"{run['name']} ({run['run_id']})" for run in runs]
    selected_run = runs[labels.index(st.selectbox("Select run", options=labels))]
    summary = selected_run["summary"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Processed", summary["processed_mails"])
    c2.metric("Injections", f"{summary['actual_injections']} / {summary['target_injections']}")
    c3.metric("Flags", f"{summary['flagged_count']} / {summary['max_flags']}")
    c4.metric("Flag rate", f"{summary['flag_rate']}%")
    c5.metric("Model", selected_run["parameters"]["model_name"])

    st.subheader("Hyperparameters")
    st.json(selected_run.get("hyperparameters", selected_run["parameters"]))

    st.subheader("Mail results")
    st.dataframe(selected_run["results"], use_container_width=True)

    if selected_run.get("audit_log"):
        st.subheader("Audit log")
        st.dataframe(selected_run["audit_log"], use_container_width=True)

    st.subheader("Run comparison")
    rows = []
    for run in runs:
        row = {
            "name": run["name"],
            "run_id": run["run_id"],
            "model_name": run["parameters"]["model_name"],
            "processed": run["summary"]["processed_mails"],
            "injections": run["summary"]["actual_injections"],
            "flags": run["summary"]["flagged_count"],
            "flag_rate": run["summary"]["flag_rate"],
            "success": run["summary"]["success"],
        }
        row.update({key: display_value(value) for key, value in run.get("hyperparameters", {}).items()})
        rows.append(row)

    if pd is None:
        st.dataframe(rows, use_container_width=True)
    else:
        df = pd.DataFrame(rows)
        metric_columns = {"name", "run_id", "processed", "injections", "flags", "flag_rate", "success"}
        hyperparameter_columns = sorted(
            column for column in df.columns if column not in metric_columns
        )
        selected_filters = st.multiselect("Filter by hyperparameters", options=hyperparameter_columns)
        filtered = df.copy()

        for column in selected_filters:
            choices = sorted(str(value) for value in filtered[column].dropna().unique())
            selected = st.multiselect(column, options=choices, default=choices)
            filtered = filtered[filtered[column].astype(str).isin(selected)]

        st.dataframe(filtered, use_container_width=True)

        if hyperparameter_columns:
            group_by = st.selectbox("Chart by hyperparameter", options=hyperparameter_columns)
            chart = filtered.groupby(group_by, dropna=False)[["injections", "flags"]].mean()
            st.bar_chart(chart)
