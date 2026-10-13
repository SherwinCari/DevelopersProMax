"""Sign-in and create-account screen (shown before the rest of the app)."""
from __future__ import annotations

import html

import psycopg
import streamlit as st

import auth
import db
import ui_theme as ui

_CSS = f"""
<style>
  /* Full-bleed auth screen: no sidebar, no top bar, no page padding */
  [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
  header[data-testid="stHeader"] {{ display: none !important; }}
  .block-container {{ padding: 0 !important; max-width: 100% !important; }}
  [data-testid="stHorizontalBlock"] {{ gap: 0 !important; }}

  /* Left brand panel */
  .st-key-auth_left {{
    background: {ui.NAVY}; min-height: 100vh; padding: 2.6rem 4rem;
    color: #fff; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .hg-auth-brand {{ display: flex; align-items: center; gap: .8rem;
    font-size: 1.7rem; font-weight: 800; letter-spacing: -.3px; }}
  .hg-auth-eyebrow {{ color: {ui.GOLD}; font-weight: 700; font-size: .8rem;
    letter-spacing: .02em; text-transform: uppercase; display: flex;
    align-items: center; gap: .8rem; margin-bottom: 1.4rem; }}
  .hg-auth-eyebrow::before {{ content: ""; width: 42px; height: 2px; background: {ui.GOLD}; }}
  .hg-auth-title {{ font-size: clamp(2.2rem, 4vw, 3.6rem); font-weight: 800;
    line-height: 1.08; letter-spacing: -1px; margin: 0 0 1.4rem; }}
  .hg-auth-title em {{ color: {ui.GOLD}; font-style: normal; }}
  .hg-auth-lead {{ color: #B9C4DD; font-size: 1.1rem; line-height: 1.7; max-width: 30rem; }}
  .hg-auth-feat {{ display: flex; align-items: center; gap: 1rem; margin-top: .9rem;
    font-size: 1.05rem; }}
  .hg-auth-feat .ico {{ width: 56px; height: 56px; border-radius: 14px;
    border: 1px solid rgba(255,255,255,.18); background: rgba(255,255,255,.05);
    display: flex; align-items: center; justify-content: center; color: {ui.GOLD}; }}

  /* Right form panel */
  .st-key-auth_right {{ background: #F7F8FB; min-height: 100vh; padding: 5rem 4rem 3rem; }}
  .st-key-auth_right > div {{ max-width: 520px; margin: 0 auto; }}
  .hg-auth-badge {{ width: 76px; height: 76px; border-radius: 20px; background: #fff;
    box-shadow: 0 6px 24px rgba(11,31,77,.08); display: flex; align-items: center;
    justify-content: center; color: {ui.NAVY}; margin-bottom: 1.6rem; }}
  .hg-auth-h {{ font-size: 2.5rem; font-weight: 800; color: {ui.NAVY};
    letter-spacing: -.8px; margin: 0 0 .4rem; line-height: 1.15; }}
  .hg-auth-sub {{ color: {ui.MUTED}; font-size: 1.1rem; margin-bottom: 1.8rem; }}
  .st-key-auth_right label p {{ font-weight: 700; color: {ui.NAVY}; font-size: .98rem; }}
  .st-key-auth_right [data-baseweb="input"], .st-key-auth_right [data-baseweb="base-input"] {{
    border-radius: 12px; }}
  .st-key-auth_right input {{ padding-top: .85rem; padding-bottom: .85rem; font-size: 1rem; }}
  .st-key-auth_right [data-testid="stFormSubmitButton"] button {{
    background: {ui.NAVY}; color: #fff; border: 0; border-radius: 12px;
    padding: .95rem 1rem; font-weight: 700; font-size: 1.05rem; }}
  .st-key-auth_right [data-testid="stFormSubmitButton"] button:hover {{
    background: {ui.NAVY_SOFT}; color: {ui.GOLD_SOFT}; }}
  .hg-auth-switch {{ text-align: center; color: {ui.MUTED}; margin-top: 1.4rem; }}

  @media (max-width: 800px) {{
    .st-key-auth_left {{ min-height: auto; padding: 2rem 1.5rem; gap: 1.5rem; }}
    .st-key-auth_right {{ min-height: auto; padding: 2rem 1.5rem; }}
  }}
</style>
"""

_FEATURE_ICONS = {
    "cap": '<path d="M2 9l10-5 10 5-10 5L2 9z"/><path d="M6 11v5c3 2 9 2 12 0v-5"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4V5z"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
}
_BOOK = '<path d="M3 5h7a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H3V5zM21 5h-7a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h7V5z"/>'


def _svg(path: str, size: int = 26) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>'
    )


def _left_panel() -> None:
    feats = [
        ("cap", "Find the program that fits you"),
        ("chat", "Get answers, not guesswork"),
        ("mic", "Practice for your admission interview"),
    ]
    feat_html = "".join(
        f'<div class="hg-auth-feat"><span class="ico">{_svg(_FEATURE_ICONS[k], 24)}</span>{html.escape(t)}</div>'
        for k, t in feats
    )
    st.markdown(
        f"""
        <div class="hg-auth-brand">{ui.brand_mark(52)}<span>HeronGuide</span></div>
        <div>
          <div class="hg-auth-eyebrow">UMak CCIS · Smart Admission Advisor</div>
          <h1 class="hg-auth-title">Your next chapter<br>starts <em>here.</em></h1>
          <p class="hg-auth-lead">A clearer path to your future. Get honest guidance and
             find where you belong at CCIS.</p>
        </div>
        <div>{feat_html}</div>
        """,
        unsafe_allow_html=True,
    )


def _switch(view: str) -> None:
    st.session_state["auth_view"] = view


def _db_error(exc: Exception) -> None:
    if isinstance(exc, db.DatabaseConfigError):
        st.error("The database isn't configured yet. Set DATABASE_URL (see README).")
    else:
        st.error("Can't reach the database right now. Check that PostgreSQL is running.")


def _login_form() -> None:
    st.markdown(
        f'<div class="hg-auth-badge">{_svg(_BOOK, 34)}</div>'
        '<h2 class="hg-auth-h">Welcome back, Heron!</h2>'
        '<div class="hg-auth-sub">Sign in to continue your CCIS journey.</div>',
        unsafe_allow_html=True,
    )
    with st.form("login_form", border=False):
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign in  →", type="primary", use_container_width=True)

    if submitted:
        try:
            user, error = auth.login(email, password)
        except (psycopg.Error, db.DatabaseConfigError) as exc:
            _db_error(exc)
            return
        if error:
            st.error(error)
        else:
            st.session_state["hg_user"] = user
            st.rerun()

    st.markdown('<div class="hg-auth-switch">Don\'t have an account?</div>', unsafe_allow_html=True)
    st.button("Create an account", on_click=_switch, args=("signup",), use_container_width=True,
              key="to_signup")


def _signup_form() -> None:
    st.markdown(
        f'<div class="hg-auth-badge">{_svg(_BOOK, 34)}</div>'
        '<h2 class="hg-auth-h">Create your account</h2>'
        '<div class="hg-auth-sub">Join HeronGuide and find your place at CCIS.</div>',
        unsafe_allow_html=True,
    )
    with st.form("signup_form", border=False):
        name = st.text_input("Full name", placeholder="Juan Dela Cruz")
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password",
                                 placeholder="At least 8 characters, with a letter and a number")
        confirm = st.text_input("Confirm password", type="password", placeholder="Re-enter your password")
        submitted = st.form_submit_button("Create account  →", type="primary", use_container_width=True)

    if submitted:
        try:
            user, error = auth.register(name, email, password, confirm)
        except (psycopg.Error, db.DatabaseConfigError) as exc:
            _db_error(exc)
            return
        if error:
            st.error(error)
        else:
            st.session_state["hg_user"] = user
            st.rerun()

    st.markdown('<div class="hg-auth-switch">Already have an account?</div>', unsafe_allow_html=True)
    st.button("Back to sign in", on_click=_switch, args=("login",), use_container_width=True,
              key="to_login")


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    view = st.session_state.setdefault("auth_view", "login")
    left, right = st.columns(2, gap="small")
    with left.container(key="auth_left"):
        _left_panel()
    with right.container(key="auth_right"):
        _login_form() if view == "login" else _signup_form()
