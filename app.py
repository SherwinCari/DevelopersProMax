"""HeronGuide — UMak CCIS Smart Admission Advisor (hackathon prototype).

Streamlit entry point. The UI flow is wired up in later tasks; this file
currently establishes the themed shell so the app launches cleanly.
"""
from __future__ import annotations

import streamlit as st

import ui_theme

st.set_page_config(
    page_title="HeronGuide — UMak CCIS Admission Advisor",
    page_icon="🦩",
    layout="centered",
)

ui_theme.inject_theme()
ui_theme.render_header()

st.info(
    "Prototype shell is live. Input form, eligibility results, and the AI "
    "advisor are wired up in the following build steps.",
    icon="🚧",
)

ui_theme.render_footer()
