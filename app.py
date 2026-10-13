"""HeronGuide — UMak CCIS Smart Admission Advisor (hackathon prototype).

Streamlit entry point: shared theme, sidebar navigation, page routing.
"""
from __future__ import annotations

import streamlit as st

import advisor
import ui_theme
from views import chat, home, programs, settings

st.set_page_config(
    page_title="HeronGuide — UMak CCIS Admission Advisor",
    page_icon="🪶",
    layout="wide",
)


@st.cache_data(ttl=30, show_spinner=False)
def _ai_up() -> bool:
    return advisor.ollama_available()


ui_theme.inject_theme()
st.session_state["hg_ai_up"] = _ai_up()

pages = [
    st.Page(home.render, title="Home", icon=":material/home:", url_path="home", default=True),
    st.Page(chat.render, title="Chat", icon=":material/chat_bubble:", url_path="chat"),
    st.Page(programs.render, title="CCIS Programs", icon=":material/school:", url_path="programs"),
    st.Page(settings.render, title="Settings", icon=":material/settings:", url_path="settings"),
]
nav = st.navigation(pages, position="hidden")

with st.sidebar:
    ui_theme.render_sidebar_brand()
    for p in pages:
        st.page_link(p)
    ui_theme.render_sidebar_identity()

nav.run()
