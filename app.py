"""HeronGuide — UMak Smart Admission Advisor (hackathon prototype).

Streamlit entry point: shared theme, sidebar navigation, page routing.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

import advisor
import auth
import cookies
import db
import ui_theme
from views import auth_page, campus_map, chat, home, programs, settings

st.set_page_config(
    page_title="HeronGuide — UMak Admission Advisor",
    page_icon=str(Path(__file__).parent / "assets" / "heronguide-logo.png"),
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
    # Restore the login from the cookie after a page refresh.
    _tok = st.context.cookies.get("hg_token")
    try:
        _user = auth.user_from_token(_tok)
    except Exception:  # noqa: BLE001
        _user = None

    if _user:
        st.session_state["hg_user"] = _user
        st.session_state["hg_token"] = _tok
    else:
        # First login-page load shows a short skeleton while the DB starts.
        first_login_load = not st.session_state.get("hg_login_bootstrapped", False)
        loading = st.empty()
        if first_login_load:
            with loading.container():
                auth_page.render_loading()

        if not _init_db():
            _init_db.clear()  # retry on the next run instead of caching the failure

        if first_login_load:
            loading.empty()
            st.session_state["hg_login_bootstrapped"] = True

        auth_page.render()
        if st.session_state.pop("hg_clear_cookie", False):
            cookies.write("hg_token", "", 0)  # expire the browser cookie after sign-out
        st.stop()

st.session_state["hg_ai_up"] = _ai_up()

pages = [
    st.Page(home.render, title="Home", icon=":material/home:", url_path="home", default=True),
    st.Page(chat.render, title="Chat", icon=":material/chat_bubble:", url_path="chat"),
    st.Page(programs.render, title="UMak Programs", icon=":material/school:", url_path="programs"),
    st.Page(settings.render, title="Settings", icon=":material/settings:", url_path="settings"),
    st.Page(campus_map.render, title="Campus Map", icon=":material/map:", url_path="campus-map"),
]

nav = st.navigation(pages, position="hidden")

# App-level header with the logo (click → Home, via st.page_link so the
# session is kept). Placed after the login gate: the auth screen never sees it.
ui_theme.render_nav_header(pages[0])

with st.sidebar:
    ui_theme.render_sidebar_brand()
    for p in pages:
        st.page_link(p)
    ui_theme.render_sidebar_identity()
    if st.button("Sign out", icon=":material/logout:", use_container_width=True):
        _tok = st.session_state.get("hg_token") or st.context.cookies.get("hg_token")
        try:
            auth.delete_session(_tok)
        except Exception:  # noqa: BLE001
            pass
        st.session_state.clear()  # also wipes grades/chat held in this session
        st.session_state["hg_clear_cookie"] = True
        st.session_state["hg_login_bootstrapped"] = True  # skip the skeleton next time
        st.rerun()

nav.run()

# Save the login cookie once, on the first run after sign-in.
if "hg_set_cookie" in st.session_state:
    cookies.write("hg_token", st.session_state.pop("hg_set_cookie"), auth.SESSION_DAYS * 86400)