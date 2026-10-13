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
  /* Full-bleed auth screen: no sidebar, no header/toolbar/decoration, no page padding */
  [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
  [data-testid="stExpandSidebarButton"], header, [data-testid="stHeader"],
  [data-testid="stAppHeader"], [data-testid="stToolbar"],
  [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
  .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
  [data-testid="stMain"] > div {{ padding-top: 0 !important; margin-top: 0 !important; }}
  .block-container, [data-testid="stMainBlockContainer"], .stMainBlockContainer {{
    padding: 0 !important; max-width: 100% !important; }}
  [data-testid="stHorizontalBlock"] {{ gap: 0 !important; }}
  /* <style> blocks are wrapped in empty element containers; they were adding a
     blank strip (flex gap) above the panels, so take them out of the layout */
  [data-testid="stElementContainer"]:has(style), .stElementContainer:has(style),
  .element-container:has(style) {{ display: none !important; }}
  [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"],
  .block-container > [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
  html, body {{ overflow-x: hidden; }}

  /* Left brand panel */
  .st-key-auth_left, .st-key-skel_left {{
    position: relative; overflow: hidden;
    background: {ui.NAVY}; min-height: 100vh; padding: 2.6rem 4rem;
    color: #fff; display: flex; flex-direction: column; justify-content: space-between;
  }}
  /* Logo as a faint background watermark */
  .st-key-auth_left::before {{
    content: ""; position: absolute; z-index: 0; pointer-events: none;
    width: min(88%, 620px); aspect-ratio: 1; right: -14%; bottom: -10%;
    background: url("{ui.logo_data_uri()}") center / contain no-repeat;
    opacity: 0.10;
  }}
  .st-key-auth_left > * {{ position: relative; z-index: 1; }}
  .hg-auth-brand {{ display: flex; align-items: center; gap: .8rem;
    font-size: 1.7rem; font-weight: 800; letter-spacing: -.3px; }}
  .hg-auth-mobile {{ display: none; }}
  .hg-auth-mobile summary {{ list-style: none; cursor: pointer; }}
  .hg-auth-mobile summary::-webkit-details-marker {{ display: none; }}
  .hg-burger {{ position: relative; width: 44px; height: 44px; border-radius: 12px;
    border: 1px solid rgba(255,255,255,.22); background: rgba(255,255,255,.06); flex: none; }}
  .hg-burger::before {{ content: ""; position: absolute; left: 12px; right: 12px; top: 14px;
    height: 2.5px; border-radius: 2px; background: {ui.GOLD};
    box-shadow: 0 7px 0 {ui.GOLD}, 0 14px 0 {ui.GOLD}; }}
  .hg-auth-mobile[open] .hg-burger {{ background: {ui.GOLD}; }}
  .hg-auth-mobile[open] .hg-burger::before {{ background: {ui.NAVY}; box-shadow: 0 7px 0 {ui.NAVY}, 0 14px 0 {ui.NAVY}; }}
  .hg-auth-mobile summary:focus-visible {{ outline: 3px solid {ui.GOLD_SOFT}; outline-offset: 3px; border-radius: 12px; }}
  .hg-mob-bar {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; }}
  .hg-mob-bar .hg-auth-brand {{ font-size: 1.35rem; }}
  .hg-mob-menu {{ padding: 1.2rem 0 .4rem; }}
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
  .st-key-auth_right, .st-key-skel_right {{ background: #F7F8FB; min-height: 100vh; padding: 3.5rem 4rem 2rem; }}
  .st-key-auth_right > div, .st-key-skel_right > div {{ max-width: 520px; margin: 0 auto; }}
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
  /* spacing inside the form panel */
  .st-key-auth_right [data-testid="stVerticalBlock"] {{ gap: 1rem; }}
  .st-key-auth_right [data-testid="stForm"] [data-testid="stVerticalBlock"] {{ gap: 1.1rem; }}
  .st-key-auth_right [data-testid="stFormSubmitButton"] {{ margin-top: .5rem; }}
  .hg-auth-switch {{ text-align: center; color: {ui.MUTED}; margin: 1.2rem 0 .2rem; }}
  .st-key-to_signup button, .st-key-to_login button {{
    min-height: 52px; border-radius: 12px; background: #fff; border: 1px solid #cfd8e8; }}

  @media (max-width: 800px) {{
    .st-key-auth_left, .st-key-skel_left {{ min-height: auto; padding: 1rem 1.25rem; }}
    .st-key-auth_left::before {{ width: 260px; right: -60px; bottom: -90px; }}
    .hg-auth-desktop {{ display: none; }}
    .hg-auth-mobile {{ display: block; }}
    .hg-auth-title {{ font-size: 2rem; }}
    .hg-auth-feat {{ font-size: 1rem; }}
    .hg-auth-feat .ico {{ width: 48px; height: 48px; }}
    .st-key-auth_right, .st-key-skel_right {{ min-height: auto; padding: 2rem 1.25rem 2.5rem; }}
    .hg-auth-badge {{ width: 64px; height: 64px; margin-bottom: 1.2rem; }}
    .hg-auth-h {{ font-size: 1.9rem; }}
    .hg-auth-sub {{ font-size: 1rem; margin-bottom: 1.3rem; }}
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
    hero = f"""
        <div>
          <div class="hg-auth-eyebrow">UMak · Smart Admission Advisor</div>
          <h1 class="hg-auth-title">Your next chapter<br>starts <em>here.</em></h1>
          <p class="hg-auth-lead">A clearer path to your future. Get honest guidance and
             find where you belong at UMak.</p>
        </div>
        <div>{feat_html}</div>
    """.strip()
    st.markdown(
        f"""
        <div class="hg-auth-desktop">
          <div class="hg-auth-brand"><span>HeronGuide</span></div>
          {hero}
        </div>
        <details class="hg-auth-mobile">
          <summary aria-label="Toggle menu">
            <div class="hg-mob-bar">
              <div class="hg-auth-brand">{ui.brand_mark(36)}<span>HeronGuide</span></div>
              <span class="hg-burger" aria-hidden="true"></span>
            </div>
          </summary>
          <div class="hg-mob-menu">{hero}</div>
        </details>
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
        '<div class="hg-auth-sub">Join HeronGuide and find your place at UMak.</div>',
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


# ADDED: Login skeleton loading screen.
# It reuses the real auth layout (same columns + same full-bleed CSS) instead of an
# iframe, so it lines up exactly with the actual login screen.

_SKEL_CSS = """
<style>
  @keyframes hg-shimmer { 0% {background-position: 200% 0;} 100% {background-position: -200% 0;} }
  .sk { border-radius: 10px; background-size: 200% 100%;
        animation: hg-shimmer 1.4s ease-in-out infinite; }
  .sk-d { background-image: linear-gradient(90deg,#1B2D5E 25%,#2B3F73 50%,#1B2D5E 75%); }
  .sk-l { background-image: linear-gradient(90deg,#E7EBF2 25%,#F8FAFF 50%,#E7EBF2 75%); }
  .sk-row { display: flex; align-items: center; gap: .8rem; }
  .sk-feat { display: flex; align-items: center; gap: 1rem; margin-top: .9rem; }
  .sk-card { background: #fff; border: 1px solid #E7EBF2; border-radius: 16px;
             padding: 1.5rem; margin-top: 1.8rem; }
  @media (prefers-reduced-motion: reduce) { .sk { animation: none; } }
</style>
"""


def _b(cls: str, w: str, h: str, extra: str = "") -> str:
    return f'<div class="sk {cls}" style="width:{w};height:{h};{extra}"></div>'


def render_loading() -> None:
    """Skeleton that reuses the real auth layout (same columns, same full-bleed CSS)."""
    st.markdown(_CSS + _SKEL_CSS, unsafe_allow_html=True)
    left, right = st.columns(2, gap="small")

    with left.container(key="skel_left"):
        st.markdown(
            '<div class="sk-row">' + _b("sk-d", "170px", "28px") + "</div>"
            + "<div>"
            + _b("sk-d", "260px", "14px", "margin-bottom:1.4rem;")
            + _b("sk-d", "75%", "52px", "margin-bottom:.8rem;")
            + _b("sk-d", "55%", "52px", "margin-bottom:1.6rem;")
            + _b("sk-d", "85%", "14px", "margin-bottom:.7rem;")
            + _b("sk-d", "60%", "14px")
            + "</div>"
            + "<div>"
            + "".join(
                '<div class="sk-feat">' + _b("sk-d", "56px", "56px", "border-radius:14px;")
                + _b("sk-d", "55%", "16px") + "</div>"
                for _ in range(3)
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    with right.container(key="skel_right"):
        st.markdown(
            _b("sk-l", "76px", "76px", "border-radius:20px;margin-bottom:1.6rem;")
            + _b("sk-l", "80%", "40px", "margin-bottom:.8rem;")
            + _b("sk-l", "65%", "16px")
            + '<div class="sk-card">'
            + _b("sk-l", "30%", "14px", "margin-bottom:.7rem;")
            + _b("sk-l", "100%", "50px", "margin-bottom:1.3rem;")
            + _b("sk-l", "25%", "14px", "margin-bottom:.7rem;")
            + _b("sk-l", "100%", "50px", "margin-bottom:1.3rem;")
            + _b("sk-l", "100%", "56px", "border-radius:12px;")
            + "</div>"
            + _b("sk-l", "40%", "16px", "margin:1.6rem auto .8rem;")
            + _b("sk-l", "100%", "52px", "border-radius:12px;"),
            unsafe_allow_html=True,
        )