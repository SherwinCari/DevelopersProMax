"""Write/expire a browser cookie from the server side of a Streamlit app.

Runs a one-line script in a 1px same-origin iframe. Unlike a Streamlit
custom component, it never sends a value back, so it can't trigger extra
reruns (which is what made sign-in/sign-out need several clicks).
"""
from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components


def write(name: str, value: str, max_age: int) -> None:
    """Set cookie ``name`` (``max_age=0`` deletes it). Call it on a run that
    stays on screen long enough for the iframe to load (i.e. not right before
    ``st.rerun()``)."""
    js = (
        "<script>try{window.parent.document.cookie="
        f"{json.dumps(name)}+'='+encodeURIComponent({json.dumps(value)})"
        f"+'; max-age={int(max_age)}; path=/; SameSite=Lax';}}catch(e){{}}</script>"
    )
    try:
        st.iframe(js, height=1)
    except Exception:  # noqa: BLE001 - older Streamlit without st.iframe
        components.html(js, height=0)
