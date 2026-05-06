"""Entry point for the Streamlit UI."""

import streamlit as st

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


navigation = st.navigation(
    [
        st.Page(home_page, title="Home", default=True),
        st.Page("pages/multiple_runs.py", title="Multiple Runs"),
        st.Page("pages/results.py", title="Results"),
    ],
    position="sidebar",
)

navigation.run()
