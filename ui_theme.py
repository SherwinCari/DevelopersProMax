"""UMak-themed styling and shared UI chrome for HeronGuide.

Centralizes the University of Makati visual identity (deep navy + gold)
so every view in the prototype stays consistent and on-brand.
"""
from __future__ import annotations

import streamlit as st

# UMak palette
NAVY = "#0B1F4D"
NAVY_SOFT = "#13295F"
GOLD = "#F2A900"
GOLD_SOFT = "#FFCB4F"
BG_SOFT = "#F3F6FB"
GREEN = "#1E8E3E"
AMBER = "#C77700"
RED = "#C5221F"

_CSS = f"""
<style>
  /* ---- base ---- */
  html, body, [class*="css"] {{
    font-family: "Segoe UI", "Inter", system-ui, sans-serif;
  }}
  .block-container {{ padding-top: 1.4rem; max-width: 1050px; }}

  /* ---- header banner ---- */
  .hg-header {{
    background: linear-gradient(135deg, {NAVY} 0%, {NAVY_SOFT} 60%, {GOLD} 220%);
    border-radius: 18px;
    padding: 1.5rem 1.8rem;
    color: #ffffff;
    box-shadow: 0 10px 30px rgba(11,31,77,0.25);
    margin-bottom: 1.2rem;
  }}
  .hg-header h1 {{
    margin: 0; font-size: 1.9rem; font-weight: 800; letter-spacing: -0.4px;
    display: flex; align-items: center; gap: 0.6rem;
  }}
  .hg-header p {{ margin: 0.35rem 0 0; opacity: 0.92; font-size: 1.02rem; }}
  .hg-logo {{
    background: {GOLD}; color: {NAVY}; border-radius: 50%;
    width: 44px; height: 44px; display: inline-flex;
    align-items: center; justify-content: center; font-size: 1.4rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }}

  /* ---- badges ---- */
  .hg-badges {{ margin-top: 0.9rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }}
  .hg-badge {{
    background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.35);
    color: #fff; padding: 0.28rem 0.7rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600;
  }}

  /* ---- result cards ---- */
  .hg-card {{
    border-radius: 14px; padding: 1rem 1.15rem; margin-bottom: 0.8rem;
    background: #fff; border: 1px solid #e4e9f2;
    box-shadow: 0 4px 14px rgba(11,31,77,0.06);
    border-left: 6px solid {NAVY};
  }}
  .hg-card.pass {{ border-left-color: {GREEN}; }}
  .hg-card.near {{ border-left-color: {AMBER}; }}
  .hg-card.fail {{ border-left-color: {RED}; }}
  .hg-card h3 {{ margin: 0 0 0.2rem; font-size: 1.08rem; color: {NAVY}; }}
  .hg-pill {{
    display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
    font-size: 0.76rem; font-weight: 700; color: #fff;
  }}
  .hg-pill.pass {{ background: {GREEN}; }}
  .hg-pill.near {{ background: {AMBER}; }}
  .hg-pill.fail {{ background: {RED}; }}
  .hg-gap {{ color: {RED}; font-size: 0.9rem; margin: 0.15rem 0; }}
  .hg-ok  {{ color: {GREEN}; font-size: 0.9rem; margin: 0.15rem 0; }}

  /* ---- advisor panel ---- */
  .hg-advisor {{
    background: {BG_SOFT}; border-radius: 14px; padding: 1.1rem 1.25rem;
    border: 1px solid #dde5f1; margin-top: 0.4rem;
  }}
  .hg-advisor .hg-title {{
    color: {NAVY}; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.4rem;
  }}

  .hg-foot {{ color: #6b7793; font-size: 0.8rem; margin-top: 2rem; text-align: center; }}
</style>
"""


def inject_theme() -> None:
    """Inject the UMak CSS. Call once at the top of the app."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header() -> None:
    """Render the branded HeronGuide header with privacy/offline badges."""
    st.markdown(
        """
        <div class="hg-header">
          <h1><span class="hg-logo">&#129517;</span> HeronGuide</h1>
          <p>UMak CCIS Smart Admission Advisor &mdash; instant eligibility, honest guidance.</p>
          <div class="hg-badges">
            <span class="hg-badge">&#128274; Privacy-first</span>
            <span class="hg-badge">&#9889; Runs locally</span>
            <span class="hg-badge">&#129504; Local AI (Ollama)</span>
            <span class="hg-badge">&#127891; CCIS Prototype</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        '<div class="hg-foot">HeronGuide &middot; Hackathon prototype &middot; '
        "Verdicts are computed by a deterministic rule engine; AI only explains them.</div>",
        unsafe_allow_html=True,
    )
