"""UMak-themed styling and shared UI chrome for HeronGuide.

Single source of truth for the navy-and-gold visual identity. Every page
imports from here, so palette, CSS and reusable renderers are never
duplicated. Call ``inject_theme()`` once near the top of ``app.py``.

Public API
----------
inject_theme, render_header, render_nav_header, render_footer, render_topbar,
render_sidebar_brand, render_sidebar_identity, page_header, status_pill,
render_result_card, render_advisor, render_state, render_source_card,
render_banner, brand_mark
"""
from __future__ import annotations

import base64
import html
import re
from functools import lru_cache
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Palette (single definition; the CSS below is generated from it)
# ---------------------------------------------------------------------------
NAVY = "#0B1F4D"
NAVY_SOFT = "#13295F"
GOLD = "#F2A900"
GOLD_SOFT = "#FFCB4F"
BG_SOFT = "#F3F6FB"
GREEN = "#1E8E3E"
AMBER = "#C77700"
RED = "#C5221F"
WHITE = "#FFFFFF"
BORDER = "#E4E9F2"
MUTED = "#6B7793"
ADVISOR_BORDER = "#DDE5F1"

FOOTER_TEXT = (
    "HeronGuide · Hackathon prototype · "
    "Verdicts are computed by a deterministic rule engine; AI only explains them."
)

# ---------------------------------------------------------------------------
# Icons (small inline SVGs, stroke = currentColor, decorative -> aria-hidden)
# ---------------------------------------------------------------------------
_ICON_PATHS = {
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "laptop": '<rect x="4" y="5" width="16" height="11" rx="1.5"/><path d="M2 20h20"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "flask": '<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2.2h12.4a1.5 1.5 0 0 0 1.3-2.2L14 9V3"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "alert": '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18h.01"/>',
}


def icon(name: str, size: int = 14) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{_ICON_PATHS[name]}</svg>'
    )


# ---------------------------------------------------------------------------
# Brand mark — the official HeronGuide logo (assets/heronguide-logo.svg)
# ---------------------------------------------------------------------------
LOGO_PATH = Path(__file__).parent / "assets" / "heronguide-logo.svg"
LOGO_PNG_PATH = Path(__file__).parent / "assets" / "heronguide-logo.png"


@lru_cache(maxsize=1)
def logo_data_uri() -> str:
    """The logo SVG as a base64 data URI (usable in <img> and CSS url())."""
    data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{data}"


def brand_mark(size: int = 44) -> str:
    """The HeronGuide logo at ``size`` px. Single source for every logo in the app."""
    return (
        f'<img class="hg-logo" src="{logo_data_uri()}" alt="HeronGuide logo" '
        f'width="{size}" height="{size}" style="width:{size}px;height:{size}px">'
    )


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_CSS = f"""
<style>
  :root {{
    --hg-navy: {NAVY}; --hg-navy-soft: {NAVY_SOFT}; --hg-gold: {GOLD};
    --hg-gold-soft: {GOLD_SOFT}; --hg-bg: {BG_SOFT}; --hg-border: {BORDER};
    --hg-muted: {MUTED}; --hg-green: {GREEN}; --hg-amber: {AMBER}; --hg-red: {RED};
    --hg-ease: 180ms ease;
  }}

  /* ---- base ---- */
  html, body, [class*="css"], .stApp {{
    font-family: "Inter", "Segoe UI", system-ui, sans-serif;
  }}
  .stApp {{ background: {BG_SOFT}; color: {NAVY}; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stDecoration"] {{ display: none; }}
  .block-container {{
    padding-top: 1rem; padding-bottom: 2rem; max-width: 1180px;
  }}
  h1, h2, h3 {{ color: {NAVY}; letter-spacing: -0.3px; }}

  /* ---- sidebar ---- */
  [data-testid="stSidebar"] {{ background: {NAVY}; }}
  /* fixed width only while open, so collapsing still works */
  [data-testid="stSidebar"][aria-expanded="true"] {{ min-width: 260px; max-width: 260px; }}
  [data-testid="stSidebar"] > div:first-child {{ background: {NAVY}; }}
  [data-testid="stSidebar"] * {{ color: #fff; }}
  [data-testid="stSidebarContent"] {{
    padding: 0 0.75rem 1rem; display: flex; flex-direction: column;
  }}
  /* Streamlit's own sidebar header: slim, with a clear close (x) button */
  [data-testid="stSidebarHeader"] {{
    padding: 0.9rem 0.25rem 0.2rem; margin-bottom: 0; height: auto; min-height: 0;
    justify-content: flex-end;
  }}
  [data-testid="stSidebarHeader"] button,
  [data-testid="stSidebarCollapseButton"] button {{
    width: 40px; height: 40px; border-radius: 10px; color: #fff;
    background: rgba(255,255,255,0.08);
  }}
  [data-testid="stSidebarHeader"] button:hover,
  [data-testid="stSidebarCollapseButton"] button:hover {{ background: rgba(255,255,255,0.18); }}
  .hg-side-brand {{
    display: flex; align-items: center; gap: 0.75rem; padding: 0.2rem 0.4rem 1.1rem;
    margin-bottom: 0.6rem; border-bottom: 1px solid rgba(255,255,255,0.12);
    font-weight: 800; font-size: 1.3rem; letter-spacing: -0.3px;
  }}
  .hg-side-brand span {{ color: #fff; line-height: 1.1; }}
  .hg-side-brand small {{
    display: block; color: {GOLD}; font-size: 0.62rem; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase; margin-top: 0.2rem;
  }}
  .hg-side-id {{
    margin-top: 1.4rem; padding: 0.9rem 0.4rem 0.6rem;
    border-top: 1px solid rgba(255,255,255,0.14);
    font-size: 0.8rem; line-height: 1.4; color: rgba(255,255,255,0.8);
  }}
  .hg-side-id strong {{ color: {GOLD_SOFT}; display: block; font-size: 0.85rem; }}
  [data-testid="stSidebar"] [data-testid="stPageLink"] {{ margin-bottom: 0.2rem; }}
  [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
    border-radius: 12px; min-height: 46px; padding: 0.55rem 0.85rem; gap: 0.7rem;
    border-left: 4px solid transparent; transition: background var(--hg-ease);
    text-decoration: none;
  }}
  [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p {{ font-weight: 600; font-size: 0.97rem; }}
  [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{ background: rgba(255,255,255,0.08); }}
  [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {{
    background: {NAVY_SOFT}; border-left-color: {GOLD}; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
  }}
  [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] p {{ font-weight: 800; }}
  [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span {{ color: {GOLD_SOFT}; }}
  [data-testid="stSidebar"] a:focus-visible {{ outline: 3px solid {GOLD_SOFT}; outline-offset: 1px; }}

  /* sidebar secondary buttons (e.g. Sign out) */
  [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] {{
    background: transparent; border: 1.5px solid {GOLD}; border-radius: 12px;
    min-height: 44px; font-weight: 700; margin-top: 0.6rem;
  }}
  [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"],
  [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] * {{ color: {GOLD_SOFT}; }}
  [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover {{
    background: {GOLD}; border-color: {GOLD};
  }}
  [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover,
  [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover * {{ color: {NAVY}; }}
  [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:focus-visible {{
    outline: 3px solid {GOLD_SOFT}; outline-offset: 2px;
  }}

  /* ---- hamburger: restyle Streamlit's sidebar-open control (stays fully functional) ---- */
  [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {{
    z-index: 1000001;
  }}
  [data-testid="stSidebarCollapsedControl"] button, button[data-testid="stExpandSidebarButton"] {{
    position: relative; width: 46px; height: 46px; border-radius: 12px;
    background: {NAVY}; border: 0; box-shadow: 0 4px 14px rgba(11,31,77,0.28);
    color: transparent; overflow: hidden;
  }}
  [data-testid="stSidebarCollapsedControl"] button > *, button[data-testid="stExpandSidebarButton"] > * {{
    visibility: hidden;
  }}
  [data-testid="stSidebarCollapsedControl"] button::before, button[data-testid="stExpandSidebarButton"]::before {{
    content: ""; position: absolute; left: 13px; right: 13px; top: 15px; height: 2.5px;
    border-radius: 2px; background: {GOLD};
    box-shadow: 0 7px 0 {GOLD}, 0 14px 0 {GOLD};
  }}
  [data-testid="stSidebarCollapsedControl"] button:hover, button[data-testid="stExpandSidebarButton"]:hover {{
    background: {NAVY_SOFT};
  }}
  [data-testid="stSidebarCollapsedControl"] button:focus-visible, button[data-testid="stExpandSidebarButton"]:focus-visible {{
    outline: 3px solid {GOLD}; outline-offset: 2px;
  }}

  /* ---- top bar ---- */
  .hg-topbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.9rem; }}
  .hg-topbar .hello {{ font-size: 1.3rem; font-weight: 800; color: {NAVY}; line-height: 1.2; }}
  .hg-topbar .sub {{ font-size: 0.85rem; color: {MUTED}; }}
  .hg-avatar {{
    width: 44px; height: 44px; border-radius: 50%; background: {NAVY}; color: {GOLD};
    display: inline-flex; align-items: center; justify-content: center; font-weight: 800;
  }}

  /* ---- header banner ---- */
  .hg-header {{
    background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 78%);
    border-radius: 18px; padding: 1.4rem 1.7rem; color: #ffffff;
    border-bottom: 3px solid {GOLD};
    box-shadow: 0 10px 28px rgba(11,31,77,0.22); margin-bottom: 1.4rem;
    display: flex; gap: 1.1rem; align-items: flex-start;
  }}
  .hg-header .txt {{ min-width: 0; }}
  .hg-header h1 {{ margin: 0; padding: 0; font-size: 1.9rem; font-weight: 800; color: #fff; line-height: 1.15; }}
  .hg-header p {{ margin: 0.3rem 0 0; opacity: 0.94; font-size: 1.02rem; color: #fff; }}
  .hg-logo {{ flex: none; display: inline-block; object-fit: contain; }}
  .hg-badges {{ margin-top: 0.9rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }}
  .hg-badge {{
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.32);
    color: #fff; padding: 0.3rem 0.75rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600;
  }}

  /* ---- page headings ---- */
  .hg-page-title {{ font-size: 2rem; font-weight: 800; color: {NAVY}; margin: 0.2rem 0 0.1rem; }}
  .hg-page-sub {{ color: {MUTED}; font-size: 1.05rem; margin-bottom: 1rem; }}

  /* ---- banners ---- */
  .hg-banner {{
    display: flex; gap: 0.6rem; align-items: center; border-radius: 12px;
    padding: 0.7rem 1rem; margin-bottom: 1.1rem; font-size: 0.95rem; color: {NAVY};
    border: 1px solid #f0d88a; background: #FFF6D8;
  }}
  .hg-banner.info {{ background: #fff; border-color: {BORDER}; }}
  .hg-banner svg {{ flex: none; }}

  /* ---- result cards ---- */
  .hg-card {{
    border-radius: 14px; padding: 1rem 1.15rem; margin-bottom: 0.8rem;
    background: #fff; border: 1px solid {BORDER};
    box-shadow: 0 4px 14px rgba(11,31,77,0.06);
    border-left: 6px solid {NAVY};
  }}
  .hg-card.pass {{ border-left-color: {GREEN}; }}
  .hg-card.near {{ border-left-color: {AMBER}; }}
  .hg-card.fail {{ border-left-color: {RED}; }}
  .hg-card.focus {{ box-shadow: 0 6px 20px rgba(11,31,77,0.14); }}
  .hg-card-head {{ display: flex; justify-content: space-between; gap: 0.6rem; align-items: center; flex-wrap: wrap; }}
  .hg-card h3 {{ margin: 0; font-size: 1.08rem; color: {NAVY}; }}
  .hg-card .meta {{ color: {MUTED}; font-size: 0.82rem; margin: 0.15rem 0 0.4rem; }}
  .hg-pill {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.2rem 0.65rem; border-radius: 999px;
    font-size: 0.76rem; font-weight: 700; color: #fff; white-space: nowrap;
  }}
  .hg-pill.pass {{ background: {GREEN}; }}
  .hg-pill.near {{ background: {AMBER}; }}
  .hg-pill.fail {{ background: {RED}; }}
  .hg-gap {{ color: {RED}; font-size: 0.9rem; margin: 0.2rem 0; }}
  .hg-ok  {{ color: {GREEN}; font-size: 0.9rem; margin: 0.2rem 0; }}
  .hg-wait {{ color: {AMBER}; font-size: 0.9rem; margin: 0.2rem 0; }}
  .hg-gap, .hg-ok, .hg-wait {{ display: flex; gap: 0.4rem; align-items: flex-start; }}
  .hg-gap svg, .hg-ok svg, .hg-wait svg {{ margin-top: 0.2rem; flex: none; }}

  /* ---- generic white panel (wraps forms) ---- */
  [data-testid="stForm"], .hg-panel {{
    background: #fff; border: 1px solid {BORDER}; border-radius: 14px;
    box-shadow: 0 4px 14px rgba(11,31,77,0.05); padding: 1.1rem 1.2rem;
  }}

  /* ---- advisor panel ---- */
  .hg-advisor {{
    background: {BG_SOFT}; border-radius: 14px; padding: 1.1rem 1.25rem;
    border: 1px solid {ADVISOR_BORDER}; margin: 0.4rem 0 1rem;
  }}
  .hg-advisor .hg-title {{ color: {NAVY}; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.4rem; }}
  .hg-advisor .body {{ color: #24325a; font-size: 0.97rem; line-height: 1.55; }}
  .hg-advisor ul {{ margin: 0.3rem 0 0.3rem 1.1rem; padding: 0; }}
  .hg-advisor .src {{ margin-top: 0.6rem; font-size: 0.78rem; color: {MUTED}; }}

  /* ---- state blocks (empty / error / insufficient) ---- */
  .hg-state {{
    text-align: center; background: #fff; border: 1px solid {BORDER};
    border-radius: 14px; padding: 2rem 1.2rem; color: {MUTED};
  }}
  .hg-state .hg-logo {{ margin-bottom: 0.7rem; }}
  .hg-state .t {{ color: {NAVY}; font-weight: 700; font-size: 1.08rem; margin-bottom: 0.2rem; }}
  .hg-state.error {{ border-color: {RED}; }}
  .hg-state.error .t {{ color: {RED}; }}

  /* ---- source / info cards ---- */
  .hg-source {{
    background: #fff; border: 1px solid {BORDER}; border-radius: 14px;
    padding: 0.9rem 1.1rem; margin-bottom: 0.7rem;
    box-shadow: 0 2px 8px rgba(11,31,77,0.04);
  }}
  .hg-source .t {{ font-weight: 700; color: {NAVY}; }}
  .hg-source .d {{ color: {MUTED}; font-size: 0.88rem; margin-top: 0.15rem; }}

  /* ---- chat ---- */
  [data-testid="stChatMessage"] {{
    background: #fff; border: 1px solid {BORDER}; border-radius: 14px;
  }}

  /* ---- widgets: buttons, inputs, focus, motion ---- */
  .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
    border-radius: 12px; min-height: 44px; font-weight: 700;
    transition: background var(--hg-ease), box-shadow var(--hg-ease), transform var(--hg-ease);
  }}
  .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"],
  .stButton > button[data-testid="stBaseButton-primary"],
  .stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"] {{
    background: {GOLD}; color: {NAVY}; border: 1px solid {GOLD};
  }}
  .stButton > button[data-testid="stBaseButton-primary"]:hover,
  .stFormSubmitButton > button[data-testid="stBaseButton-primaryFormSubmit"]:hover {{
    background: {GOLD_SOFT}; border-color: {GOLD_SOFT}; color: {NAVY};
  }}
  .stButton > button:active, .stFormSubmitButton > button:active {{ transform: translateY(1px); }}
  .stButton > button:disabled, .stFormSubmitButton > button:disabled {{ opacity: 0.5; }}
  .stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible,
  input:focus-visible, [data-baseweb="select"] *:focus-visible {{
    outline: 3px solid {NAVY_SOFT}; outline-offset: 2px;
  }}
  [data-baseweb="input"], [data-baseweb="select"] > div {{
    border-radius: 12px; background: #fff !important; border: 1px solid #cfd8e8 !important;
  }}
  [data-baseweb="input"] > div {{ background: #fff; }}

  .hg-foot {{ color: {MUTED}; font-size: 0.8rem; margin-top: 2.2rem; text-align: center; }}

  /* ---- app-level nav header: logo + "HeronGuide" title, links Home in-app ----
     Uses st.page_link so navigation stays inside Streamlit's session (a raw
     anchor would reload the browser and drop the login state). Flat look —
     no pill, border or shadow, deliberately readable as a title, not a button. */
  .st-key-hg_topnav {{
    display: flex; align-items: center; margin-bottom: 0.1rem;
  }}
  .st-key-hg_topnav [data-testid="stPageLink-NavLink"] {{
    display: inline-flex; align-items: center; gap: 0.6rem;
    font-size: 1.18rem; font-weight: 800; letter-spacing: -0.3px;
    color: {NAVY} !important;
    padding: 0.15rem; border-radius: 10px;
    transition: opacity var(--hg-ease);
  }}
  .st-key-hg_topnav [data-testid="stPageLink-NavLink"]::before {{
    content: ""; flex: none; width: 38px; height: 38px;
    background: url("{logo_data_uri()}") center / contain no-repeat;
  }}
  .st-key-hg_topnav [data-testid="stPageLink-NavLink"]:hover {{
    opacity: 0.82;
  }}
  .st-key-hg_topnav a:focus-visible {{
    outline: 3px solid {NAVY_SOFT}; outline-offset: 2px;
  }}
  .st-key-hg_topnav .hg-nav-tagline {{
    margin-top: 0.1rem; text-align: right;
    color: {MUTED}; font-size: 0.86rem; line-height: 1.3;
  }}
  @media (max-width: 640px) {{
    .st-key-hg_topnav .hg-nav-tagline {{ display: none; }}
  }}

  @media (max-width: 900px) {{
    /* sidebar becomes an overlay drawer; keep it readable and dim the page behind it */
    [data-testid="stSidebar"][aria-expanded="true"] {{
      min-width: min(300px, 86vw); max-width: min(300px, 86vw);
      box-shadow: 8px 0 32px rgba(11,31,77,0.35);
    }}
    .block-container {{ padding-top: 4rem; }}
  }}
  @media (max-width: 640px) {{
    .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
    .hg-header {{ padding: 1.1rem 1.1rem; flex-direction: column; }}
    .hg-header h1 {{ font-size: 1.6rem; }}
    .hg-page-title {{ font-size: 1.6rem; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; animation: none !important; }}
  }}
</style>
"""


def inject_theme() -> None:
    """Inject the UMak CSS. Call once at the top of the app."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Text helper: escape LLM / user text, then allow only simple bullets & bold
# ---------------------------------------------------------------------------
def safe_html(text: str) -> str:
    out: list[str] = []
    in_list = False
    for raw in text.strip().splitlines():
        line = html.escape(raw.strip())
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        m = re.match(r"^[-*•]\s+(.*)$", line)
        if m:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{m.group(1)}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if line:
            out.append(f"<p style='margin:0.25rem 0'>{line}</p>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


# ---------------------------------------------------------------------------
# Shared chrome
# ---------------------------------------------------------------------------
def render_header(local_ai: bool = True) -> None:
    """Branded HeronGuide banner with the four trust badges.

    ``local_ai`` is False when Ollama is not reachable, so the badge never
    claims local AI that isn't actually running.
    """
    ai_badge = (
        f'{icon("cpu")} Local AI (Ollama)' if local_ai else f'{icon("alert")} Local AI unavailable'
    )
    st.markdown(
        f"""
        <header class="hg-header">
          {brand_mark(56)}
          <div class="txt">
            <h1>HeronGuide</h1>
            <p>UMak CCIS Smart Admission Advisor &mdash; instant eligibility, honest guidance.</p>
            <div class="hg-badges">
              <span class="hg-badge">{icon("lock")} Privacy-first</span>
              <span class="hg-badge">{icon("laptop")} Runs locally</span>
              <span class="hg-badge">{ai_badge}</span>
              <span class="hg-badge">{icon("flask")} CCIS Prototype</span>
            </div>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(f'<div class="hg-foot">{html.escape(FOOTER_TEXT)}</div>', unsafe_allow_html=True)


def render_nav_header(home_page) -> None:
    """App-level header: logo + "HeronGuide" title, clicking it goes Home.

    ``home_page`` is the ``st.Page`` for Home. Rendering uses ``st.page_link``
    so the click is handled by Streamlit's router without a browser reload —
    a raw anchor would reload the page, drop session state, and bounce the
    user back to the login screen. Styled flat (no pill/button look). Rendered
    after the login gate in ``app.py``, so the auth screen never shows it.
    """
    with st.container(key="hg_topnav"):
        left, right = st.columns([1, 2], gap="small")
        with left:
            st.page_link(home_page, label="HeronGuide")
        with right:
            st.markdown(
                '<div class="hg-nav-tagline">UMak CCIS Smart Admission Advisor</div>',
                unsafe_allow_html=True,
            )


def render_topbar(name: str | None = None, subtitle: str = "UMak Student") -> None:
    if not name:
        full = (st.session_state.get("hg_user") or {}).get("full_name", "")
        name = full.split()[0] if full.strip() else "Heron"
    st.markdown(
        f"""
        <div class="hg-topbar">
          <div><div class="hello">Hello, {html.escape(name)}!</div>
               <div class="sub">{html.escape(subtitle)}</div></div>
          <span class="hg-avatar" aria-label="Profile">{html.escape(name[:1].upper())}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.markdown(
        f'<div class="hg-side-brand">{brand_mark(44)}<span>HeronGuide<small>UMak CCIS</small></span></div>',
        unsafe_allow_html=True,
    )


def render_sidebar_identity() -> None:
    st.markdown(
        '<div class="hg-side-id"><strong>University of Makati</strong>'
        "College of Computing &amp; Information Sciences</div>",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f'<h2 class="hg-page-title">{html.escape(title)}</h2>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="hg-page-sub">{html.escape(subtitle)}</div>', unsafe_allow_html=True)


def render_banner(message_html: str, kind: str = "warn") -> None:
    """``message_html`` must be trusted markup (callers pass static strings)."""
    ic = "alert" if kind == "warn" else "info"
    st.markdown(
        f'<div class="hg-banner {kind}" role="note">{icon(ic, 18)}<span>{message_html}</span></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Status + result cards
# ---------------------------------------------------------------------------
_STATUS = {
    "pass": ("check", "Qualified"),
    "near": ("clock", "Pending UMCET"),
    "fail": ("x", "Not yet qualified"),
}


def status_pill(kind: str, label: str | None = None) -> str:
    ic, default = _STATUS[kind]
    return f'<span class="hg-pill {kind}">{icon(ic, 12)} {html.escape(label or default)}</span>'


def render_result_card(
    name: str,
    meta: str,
    kind: str,
    ok_lines: list[str] | None = None,
    wait_lines: list[str] | None = None,
    gap_lines: list[str] | None = None,
    focus: bool = False,
) -> None:
    """One program verdict. ``kind`` is 'pass' | 'near' | 'fail'.

    Status is conveyed by text + icon, never colour alone.
    """
    rows = "".join(f'<div class="hg-ok">{icon("check")}<span>{html.escape(t)}</span></div>' for t in ok_lines or [])
    rows += "".join(f'<div class="hg-wait">{icon("clock")}<span>{html.escape(t)}</span></div>' for t in wait_lines or [])
    rows += "".join(f'<div class="hg-gap">{icon("x")}<span>{html.escape(t)}</span></div>' for t in gap_lines or [])
    st.markdown(
        f"""
        <div class="hg-card {kind}{' focus' if focus else ''}">
          <div class="hg-card-head"><h3>{html.escape(name)}</h3>{status_pill(kind)}</div>
          <div class="meta">{html.escape(meta)}</div>
          {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_advisor(title: str, body: str, source_note: str = "") -> None:
    note = f'<div class="src">{html.escape(source_note)}</div>' if source_note else ""
    st.markdown(
        f'<section class="hg-advisor"><div class="hg-title">{html.escape(title)}</div>'
        f'<div class="body">{safe_html(body)}</div>{note}</section>',
        unsafe_allow_html=True,
    )


def render_state(kind: str, title: str, body: str = "") -> None:
    """kind: 'empty' | 'error' | 'insufficient'."""
    lead = brand_mark(48) if kind == "empty" else icon("alert" if kind == "error" else "info", 28)
    st.markdown(
        f'<div class="hg-state {kind}" role="status">{lead}'
        f'<div class="t">{html.escape(title)}</div><div>{html.escape(body)}</div></div>',
        unsafe_allow_html=True,
    )


def render_source_card(title: str, description: str) -> None:
    st.markdown(
        f'<div class="hg-source"><div class="t">{html.escape(title)}</div>'
        f'<div class="d">{html.escape(description)}</div></div>',
        unsafe_allow_html=True,
    )

def render_skeleton(lines: int = 3, title: str | None = None) -> None:
    """Render animated loading placeholders using the shared HeronGuide theme."""
    lines = max(1, min(int(lines), 8))
    heading = (
        f'<div class="hg-skeleton-heading">{html.escape(title)}</div>'
        if title else ""
    )
    placeholders = "".join(
        f'<div class="hg-skeleton-line line-{i + 1}"></div>'
        for i in range(lines)
    )

    st.markdown(
        f'''
        <style>
          @keyframes hg-skeleton-shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
          }}

          .hg-skeleton-card {{
            padding: 1rem 1.1rem;
            margin: 0.4rem 0 0.8rem;
            border: 1px solid {BORDER};
            border-radius: 14px;
            background: {WHITE};
            box-shadow: 0 4px 14px rgba(11,31,77,0.04);
          }}

          .hg-skeleton-heading {{
            width: 46%;
            height: 19px;
            margin: 0 0 1rem;
            border-radius: 6px;
            background: #e8edf5;
          }}

          .hg-skeleton-line {{
            height: 12px;
            margin: 12px 0;
            border-radius: 6px;
            background: linear-gradient(
              90deg, #edf1f7 25%, #f8faff 50%, #edf1f7 75%
            );
            background-size: 200% 100%;
            animation: hg-skeleton-shimmer 1.35s ease-in-out infinite;
          }}

          .hg-skeleton-line.line-2 {{ width: 88%; }}
          .hg-skeleton-line.line-3 {{ width: 72%; }}
          .hg-skeleton-line.line-4 {{ width: 82%; }}
          .hg-skeleton-line.line-5 {{ width: 63%; }}
          .hg-skeleton-line.line-6 {{ width: 78%; }}
          .hg-skeleton-line.line-7 {{ width: 58%; }}
          .hg-skeleton-line.line-8 {{ width: 85%; }}

          @media (prefers-reduced-motion: reduce) {{
            .hg-skeleton-line {{ animation: none; }}
          }}
        </style>

        <div class="hg-skeleton-card"
             role="status" aria-label="Loading content">
          {heading}
          {placeholders}
        </div>
        ''',
        unsafe_allow_html=True,
    )
