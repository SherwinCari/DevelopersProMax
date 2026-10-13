"""CCIS Programs: catalog browser (read-only view of data/programs.py)."""
from __future__ import annotations

import html

import streamlit as st

import ui_theme as ui
from data.programs import all_programs


def _fmt(v) -> str:
    return "—" if v is None else f"{v:g}"


def render() -> None:
    ui.render_topbar()
    ui.render_header(local_ai=st.session_state.get("hg_ai_up", True))
    ui.page_header("CCIS Programs", "Programs and the cutoffs the advisor checks against.")
    ui.render_banner("Cutoffs are <strong>demonstration data</strong> from the supplied requirements document.")
    for p in all_programs():
        umcet = p.umcet_min_tier.label if p.umcet_min_tier is not None else "—"
        track = " / ".join(p.preferred_track) or "Any strand"
        _program_card(p, umcet, track)
    ui.render_source_card(
        "Source",
        "CCIS “College Requirements” PDF and the project spec provided to this prototype. "
        "No official UMak link is bundled; verify with the UMak Admissions Office.",
    )
    ui.render_footer()


def _program_card(p, umcet: str, track: str) -> None:
    rows = "".join(
        f'<div class="hg-ok">{ui.icon("check")}<span>{html.escape(t)}</span></div>'
        for t in (
            f"GWA ≥ {_fmt(p.gwa_min)}",
            f"Math ≥ {_fmt(p.math_min)}",
            f"English ≥ {_fmt(p.english_min)}",
            f"UMCET ≥ {umcet}",
        )
    )
    st.markdown(
        f'<div class="hg-card"><div class="hg-card-head"><h3>{html.escape(p.name)}</h3>'
        f'<span class="hg-pill" style="background:{ui.NAVY}">{html.escape(p.type.label)}</span></div>'
        f'<div class="meta">Preferred SHS strand: {html.escape(track)}</div>{rows}</div>',
        unsafe_allow_html=True,
    )
