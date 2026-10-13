"""Tests for the advisor's deterministic fallback text (Task 4).

These exercise the fallback path only (no live Ollama needed), focusing on the
tone/correctness contract: the message must match the actual verdict.
"""
from __future__ import annotations

from advisor import _fallback_explain
from data.programs import UMCETTier
from rules import Status, StudentInput, alternatives, evaluate


def _student(**kw) -> StudentInput:
    base = dict(
        gwa=90.0, math=90.0, english=90.0, shs_track="STEM",
        umcet_tier=UMCETTier.AVERAGE, umcet_received=True,
    )
    base.update(kw)
    return StudentInput(**base)


def _fallback_for(student: StudentInput) -> str:
    results = evaluate(student)
    qualified = [r for r in results if r.status is Status.QUALIFIED]
    pending = [r for r in results if r.status is Status.PENDING_UMCET]
    return _fallback_explain(qualified, pending, alternatives(results), results)


def test_degree_qualified_is_celebratory():
    text = _fallback_for(_student()).lower()
    assert "great news" in text
    assert "computer science" in text


def test_degree_miss_with_diploma_alt_is_empathetic_not_celebratory():
    # Build a focused scenario (CCIS only) so the message tone does not depend on
    # unrelated colleges in the full catalog: the one degree is missed by 1% on
    # Math, and the only remaining option is a diploma. The fallback must then be
    # empathetic (not a "great news" celebration of the diploma).
    from data.programs import get_program
    from rules import Gap, ProgramResult

    cs = get_program("BSCS")
    dad = get_program("DAD")
    degree_fail = ProgramResult(
        program=cs,
        status=Status.NOT_QUALIFIED,
        gaps=[Gap("Math", "84", "85", "Math 84 is below the required 85")],
    )
    diploma_ok = ProgramResult(program=dad, status=Status.QUALIFIED, gaps=[])
    results = [degree_fail, diploma_ok]

    text = _fallback_explain([diploma_ok], [], [diploma_ok], results)
    low = text.lower()
    assert "great news" not in low            # must NOT celebrate the diploma
    assert "don't give up" in low              # empathetic alternative-path tone
    assert "Math 84 is below the required 85" in text  # exact gap named
    assert "Diploma" in text                   # routes to an alternative


def test_pending_umcet_degree_message():
    text = _fallback_for(_student(umcet_received=False, umcet_tier=None)).lower()
    assert "once you receive your umcet" in text


def test_no_program_at_all_points_to_admissions():
    # Fails even the diploma GWA baseline.
    text = _fallback_for(
        _student(gwa=70.0, math=70.0, english=70.0,
                 umcet_tier=UMCETTier.BELOW_AVERAGE)
    ).lower()
    assert "admissions office" in text
