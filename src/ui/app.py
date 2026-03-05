"""Entry point for the Streamlit UI.

This file defines the global page configuration and the sidebar navigation that routes
between the Home page and the three functional pages.
"""

import streamlit as st

# Configure browser tab metadata and a wide content layout for dashboard-like pages.
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

- Open `Single Run` to execute one run (simulation or live challenge).
- Open `Multi Run` to execute several runs in a batch.
- Open `Results` to inspect new runs and import legacy `data/results*.json` files.
"""
    )


# Define the navigation tree explicitly so sidebar labels are fully controlled.
# Using st.Page(...) avoids accidental renaming due to file-name parsing.
navigation = st.navigation(
    [
        # Home page is implemented as a callable function and marked as default.
        st.Page(home_page, title="Home", icon="🏠", default=True),
        # Functional pages are loaded from files in src/ui/pages.
        st.Page("pages/1_Single_Run.py", title="Single Run", icon="🧪"),
        st.Page("pages/2_Multi_Run.py", title="Multi Run", icon="📚"),
        st.Page("pages/3_Results.py", title="Results", icon="📈"),
    ],
    # Sidebar position mirrors the default Streamlit multipage UX.
    position="sidebar",
)

# Execute the selected page script for the current request cycle.
navigation.run()
