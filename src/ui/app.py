"""Entry point for the Streamlit UI.

This file defines the global page configuration and the sidebar navigation that routes
between the Home page and the three functional pages.
"""

import sys
from pathlib import Path

import streamlit as st

# Configure logging once at app startup before any engine module runs.
_src = str(Path(__file__).resolve().parents[1])
if _src not in sys.path:
    sys.path.insert(0, _src)
try:
    from src.config import setup_logging
except ModuleNotFoundError:
    from config import setup_logging
setup_logging()

st.set_page_config(page_title="EvalsLangchain UI", page_icon="📊", layout="wide")


def home_page() -> None:
    """Render the home landing page.

    The content here is intentionally lightweight: the user should navigate to one
    of the specialized pages from the sidebar. We keep the instructions explicit so
    first-time users understand where each task lives.
    """

    # Main page title shown in the content area.
    st.write("# Welcome to EvalsLangchain")

    # Sidebar hint in the same style as Streamlit's official multipage examples.
    st.sidebar.success("Select a page above.")

    # Short overview of what each page is responsible for.
    st.markdown(
        """
This app uses Streamlit's built-in sidebar navigation.

- Open `Multi Automatic Run` to run all parameter combinations automatically.
"""
    )


navigation = st.navigation(
    [
        st.Page(home_page, title="Home", icon="🏠", default=True),
        st.Page("pages/3_Multi_Auto_Run.py", title="Multi Automatic Run", icon="📚"),
    ],
    position="sidebar",
)

# Execute the selected page script for the current request cycle.
navigation.run()
