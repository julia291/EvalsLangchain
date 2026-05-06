"""Entry point for the Streamlit UI."""

from pathlib import Path
import sys

import streamlit as st

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.ui.engine.validation import validate_project

st.set_page_config(page_title="EvalsLangchain UI", page_icon="E", layout="wide")


def home_page() -> None:
    """Render a lightweight home page."""
    st.write("# EvalsLangchain")
    st.markdown(
        """
Use `Multiple Runs` to execute automatic live sweeps over parameter combinations.
Use `Results` to inspect and compare saved live runs.
"""
    )
    with st.expander("Project diagnostics"):
        if st.button("Run validation"):
            report = validate_project()
            if report.ok:
                st.success("Validation passed.")
            else:
                st.error("Validation found issues.")
            st.dataframe(report.as_rows(), use_container_width=True)


navigation = st.navigation(
    [
        st.Page(home_page, title="Home", default=True),
        st.Page("pages/multiple_runs.py", title="Multiple Runs"),
        st.Page("pages/results.py", title="Results"),
    ],
    position="sidebar",
)

navigation.run()
