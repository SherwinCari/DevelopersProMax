"""Settings: local-AI status, privacy notes, session reset."""
from __future__ import annotations

import streamlit as st

import advisor
import ui_theme as ui


def render() -> None:
    ui.render_topbar()
    ui.render_header(local_ai=st.session_state.get("hg_ai_up", True))
    ui.page_header("Settings", "Local AI status and privacy.")

    up = st.session_state.get("hg_ai_up", False)
    ui.render_advisor(
        "Local AI (Ollama)",
        f"Model: **{advisor.MODEL}**\n"
        + ("Status: **connected** — explanations come from your own machine."
           if up else
           "Status: **not reachable** — the app still works; explanations use built-in text. "
           "Start Ollama and run `ollama pull " + advisor.MODEL + "`."),
    )
    if st.button("Re-check connection"):
        st.cache_data.clear()
        st.rerun()

    ui.render_advisor(
        "Privacy",
        "- Grades you enter are kept only in this browser session.\n"
        "- Nothing is sent to an online AI service; the model runs through your local Ollama.\n"
        "- “Runs locally” is true only while Ollama is running on this computer.",
    )
    if st.button("Clear my session data"):
        for k in [k for k in st.session_state if k.startswith(("in_", "hg_eval", "hg_chat"))]:
            del st.session_state[k]
        st.success("Session data cleared.")
    ui.render_footer()
