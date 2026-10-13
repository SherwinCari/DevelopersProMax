"""Campus Map: embeds the standalone UMak 3D campus map."""
from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import ui_theme as ui

_MAP_FILE = Path(__file__).resolve().parent.parent / "assets" / "UMak_3D_Campus_Map.html"


@st.cache_data(show_spinner=False)
def _load_map() -> str:
    return _MAP_FILE.read_text(encoding="utf-8")


def render() -> None:
    ui.render_topbar()
    ui.render_header(local_ai=st.session_state.get("hg_ai_up", True))
    ui.page_header("Campus Map", "Explore the UMak campus in 3D.")
    components.html(_load_map(), height=720, scrolling=False)
    ui.render_footer()