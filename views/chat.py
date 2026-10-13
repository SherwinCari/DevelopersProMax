"""Chat: general CCIS questions answered by the local model (no verdicts)."""
from __future__ import annotations

import streamlit as st

import advisor
import ui_theme as ui


def render() -> None:
    ui.render_topbar()
    ui.render_header(local_ai=st.session_state.get("hg_ai_up", True))
    ui.page_header("Ask HeronGuide", "General questions only — eligibility verdicts come from the advisor on Home.")
    ui.render_banner(
        "Answers come from your local Ollama model and may be wrong. "
        "Always confirm with the UMak Admissions Office.",
        kind="info",
    )
    history = st.session_state.setdefault("hg_chat", [])
    if not history:
        ui.render_state("empty", "No messages yet", "Try: “What is the difference between BSIT and BSCS?”")
    for m in history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("note"):
                st.caption(m["note"])

    q = st.chat_input("Ask about CCIS admission…")
    if q:
        history.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                ans, used_ai = advisor.chat_answer(q)
            st.markdown(ans)
            note = "" if used_ai else "Local AI unavailable — built-in reply."
            if note:
                st.caption(note)
        history.append({"role": "assistant", "content": ans, "note": note})
    ui.render_footer()
