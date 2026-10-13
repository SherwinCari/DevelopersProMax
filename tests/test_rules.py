"""Tests for the deterministic rule engine (Task 3). Written test-first."""
from __future__ import annotations

from data.programs import UMCETTier, get_program
from rules import Status, StudentInput, alternatives, evaluate, result_for


def _student(**kw) -> StudentInput:
    base = dict(
        gwa=90.0,
        math=90.0,
        english=90.0,
        shs_track="STEM",
        umcet_tier=UMCETTier.AVERAGE,
        umcet_received=True,
    )
    base.update(kw)
    return StudentInput(**base)


def test_fully_qualified_degree():
    results = evaluate(_student())
    cs = result_for(results, "BSCS")
    assert cs.status is Status.QUALIFIED
    assert cs.gaps == []


def test_fail_by_one_percent_math_gives_exact_gap():
    results = evaluate(_student(math=84.0))
    cs = result_for(results, "BSCS")
    assert cs.status is Status.NOT_QUALIFIED
    math_gaps = [g for g in cs.gaps if g.field == "Math"]
    assert len(math_gaps) == 1
    g = math_gaps[0]
    assert "84" in g.message and "85" in g.message


def test_english_cutoff_is_83():
    # English 83 passes, 82 fails (per CCIS PDF)
    assert result_for(evaluate(_student(english=83.0)), "BSCS").status is Status.QUALIFIED
    cs = result_for(evaluate(_student(english=82.0)), "BSCS")
    assert cs.status is Status.NOT_QUALIFIED
    assert any(g.field == "English" for g in cs.gaps)


def test_below_average_umcet_disqualifies_degree_but_diploma_ok():
    student = _student(umcet_tier=UMCETTier.BELOW_AVERAGE)
    results = evaluate(student)
    cs = result_for(results, "BSCS")
    assert cs.status is Status.NOT_QUALIFIED
    assert any(g.field == "UMCET" for g in cs.gaps)
    # diploma accepts below average + 80 GWA baseline
    dad = result_for(results, "DAD")
    assert dad.status is Status.QUALIFIED
    # alternatives() surfaces the diploma(s)
    alts = alternatives(results)
    assert any(r.program.code == "DAD" for r in alts)


def test_umcet_not_received_is_pending_not_fail():
    student = _student(umcet_received=False, umcet_tier=None)
    cs = result_for(evaluate(student), "BSCS")
    assert cs.status is Status.PENDING_UMCET
    # grades passed, so no UMCET gap recorded while pending
    assert all(g.field != "UMCET" for g in cs.gaps)


def test_umcet_not_received_with_failing_grade_still_not_qualified():
    student = _student(umcet_received=False, umcet_tier=None, gwa=70.0)
    # gwa below 75 bound is still evaluated as a gap by the engine
    cs = result_for(evaluate(student), "BSCS")
    assert cs.status is Status.NOT_QUALIFIED


def test_shs_track_is_not_a_gate():
    # Non-preferred track must NOT disqualify; only flips preferred_track_met.
    results = evaluate(_student(shs_track="HUMSS"))
    cs = result_for(results, "BSCS")
    assert cs.status is Status.QUALIFIED
    assert cs.preferred_track_met is False
    # a preferred track sets the flag true
    results2 = evaluate(_student(shs_track="STEM"))
    assert result_for(results2, "BSCS").preferred_track_met is True


def test_diploma_below_80_gwa_not_qualified():
    student = _student(gwa=79.0, math=50.0, english=50.0,
                       umcet_tier=UMCETTier.BELOW_AVERAGE)
    dad = result_for(evaluate(student), "DAD")
    assert dad.status is Status.NOT_QUALIFIED
    assert any(g.field == "GWA" for g in dad.gaps)


def test_evaluate_returns_all_catalog_programs():
    results = evaluate(_student())
    codes = {r.program.code for r in results}
    assert {"BSCS", "BSIT", "BSIS", "DAD", "DCNA"}.issubset(codes)


def test_result_program_objects_are_catalog_programs():
    results = evaluate(_student())
    assert result_for(results, "BSCS").program is get_program("BSCS")
