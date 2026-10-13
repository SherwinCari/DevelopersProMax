"""Tests for the program catalog data model (Task 2)."""
from __future__ import annotations

from data.programs import (
    CCIS,
    ProgramType,
    UMCETTier,
    all_programs,
    get_program,
    programs_for,
)


def test_umcet_tier_ordering_low_to_high():
    # The catalog uses an expanded 8-tier scale (covering all colleges). What
    # the rule engine depends on is the relative ordering of the tiers it uses.
    assert (
        UMCETTier.BELOW_AVERAGE
        < UMCETTier.LOW_AVERAGE
        < UMCETTier.AVERAGE
        < UMCETTier.HIGH_AVERAGE
        < UMCETTier.EXCELLENT
    )
    labels = UMCETTier.ordered_labels()
    # ordered_labels() must be sorted low -> high and contain the core tiers.
    assert labels == [t.label for t in sorted(UMCETTier)]
    for core in ("Below Average", "Low Average", "Average", "High Average", "Excellent"):
        assert core in labels


def test_umcet_from_label_roundtrip():
    for tier in UMCETTier:
        assert UMCETTier.from_label(tier.label) is tier
    # case-insensitive
    assert UMCETTier.from_label("low average") is UMCETTier.LOW_AVERAGE


def test_ccis_has_five_programs():
    progs = programs_for(CCIS)
    assert len(progs) == 5
    codes = {p.code for p in progs}
    assert codes == {"BSCS", "BSIT", "BSIS", "DAD", "DCNA"}


def test_every_program_has_required_fields():
    for p in all_programs():
        assert p.code and p.name and p.college
        assert isinstance(p.type, ProgramType)
        # Across all colleges, programs always have a GWA floor and a UMCET floor.
        # Per-subject cutoffs (Math/English) are program-specific: some degrees
        # (e.g. arts programs) screen via portfolio/skills test instead, so
        # math_min / english_min may legitimately be None.
        assert p.gwa_min is not None
        assert p.umcet_min_tier is not None


def test_degree_cutoffs_match_pdf():
    cs = get_program("BSCS")
    assert cs.gwa_min == 85.0
    assert cs.math_min == 85.0
    assert cs.english_min == 83.0
    assert cs.umcet_min_tier is UMCETTier.LOW_AVERAGE


def test_diploma_baseline():
    for code in ("DAD", "DCNA"):
        d = get_program(code)
        assert d.type is ProgramType.DIPLOMA
        assert d.gwa_min == 80.0
        assert d.umcet_min_tier is UMCETTier.BELOW_AVERAGE
