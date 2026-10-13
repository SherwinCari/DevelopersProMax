
"""HeronGuide — UMak Smart Admission Advisor (hackathon prototype).

Streamlit entry point: shared theme, sidebar navigation, page routing.
"""
from __future__ import annotations

import time
from pathlib import Path

import streamlit as st
import advisor
import db
import ui_theme
from views import auth_page, chat, home, programs, settings
from views import auth_page, campus_map, chat, home, programs, settings

st.set_page_config(
    page_title="HeronGuide — UMak CCIS Admission Advisor",
    page_icon=str(Path(__file__).parent / "assets" / "heronguide-logo.png"),
    page_title="HeronGuide — UMak Admission Advisor",
    page_icon=str(ui_theme.LOGO_PNG_PATH),
    layout="wide",
)


@st.cache_data(ttl=30, show_spinner=False)
def _ai_up() -> bool:
    return advisor.ollama_available()


@st.cache_resource(show_spinner=False)
def _init_db() -> bool:
    """Create the tables on first run. Returns False if the DB is unreachable."""
    try:
        db.ensure_schema()
        return True
    except Exception:  # noqa: BLE001 - the login page shows a friendly error
        return False


ui_theme.inject_theme()

# ---- Login gate: nothing below runs until the user has signed in ----
if "hg_user" not in st.session_state:
    # ADDED: determine whether this is the first login-page load.
    first_login_load = not st.session_state.get(
        "hg_login_bootstrapped", False
    )

    # ADDED: display the login skeleton before database initialization.
    loading = st.empty()

    if first_login_load:
        with loading.container():
            auth_page.render_loading()

    if not _init_db():
        _init_db.clear()  # retry on the next run instead of caching the failure

    # ADDED: keep the skeleton visible for at least 2 seconds for your demo.
    if first_login_load:
        time.sleep(max(0, 2))
        loading.empty()
        st.session_state["hg_login_bootstrapped"] = True

    # Original login page remains unchanged.
    auth_page.render()
    st.stop()

st.session_state["hg_ai_up"] = _ai_up()

pages = [
    st.Page(home.render, title="Home", icon=":material/home:", url_path="home", default=True),
    st.Page(chat.render, title="Chat", icon=":material/chat_bubble:", url_path="chat"),
    st.Page(programs.render, title="CCIS Programs", icon=":material/school:", url_path="programs"),
    st.Page(settings.render, title="Settings", icon=":material/settings:", url_path="settings"),
    st.Page(campus_map.render, title="Campus Map", icon=":material/map:", url_path="campus-map"),
]

nav = st.navigation(pages, position="hidden")

with st.sidebar:
    ui_theme.render_sidebar_brand()
    for p in pages:
        st.page_link(p)
    ui_theme.render_sidebar_identity()
    if st.button("Sign out", icon=":material/logout:", use_container_width=True):
        st.session_state.clear()  # also wipes grades/chat held in this session
        st.rerun()

nav.run()
