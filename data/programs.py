"""Program catalog data model for HeronGuide.

Design goals
------------
* **Data-driven:** eligibility cutoffs live here, not in the rule engine, so
  admissions staff can adjust thresholds without touching logic.
* **Extensible:** the catalog is keyed by college -> list[Program]. CCIS is
  seeded now; the other UMak colleges can be added later with no code changes.
* **Deterministic:** UMCET tiers are an ordered enum so the rule engine can do
  a simple ``>=`` comparison.

Sources: the provided CCIS "College Requirements" PDF and the project
``kiro_hackathon_spec.md``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class UMCETTier(IntEnum):
    """UMak entrance exam rating tiers, ordered low -> high.

    IntEnum lets the rule engine compare tiers directly (e.g.
    ``student_tier >= program.umcet_min_tier``).
    """

    BELOW_AVERAGE = 0
    LOW_AVERAGE = 1
    AVERAGE = 2
    HIGH_AVERAGE = 3
    EXCELLENT = 4

    @property
    def label(self) -> str:
        return {
            UMCETTier.BELOW_AVERAGE: "Below Average",
            UMCETTier.LOW_AVERAGE: "Low Average",
            UMCETTier.AVERAGE: "Average",
            UMCETTier.HIGH_AVERAGE: "High Average",
            UMCETTier.EXCELLENT: "Excellent",
        }[self]

    @classmethod
    def from_label(cls, label: str) -> "UMCETTier":
        for tier in cls:
            if tier.label.lower() == label.strip().lower():
                return tier
        raise ValueError(f"Unknown UMCET tier label: {label!r}")

    @classmethod
    def ordered_labels(cls) -> list[str]:
        """Labels from lowest to highest, for UI selectors."""
        return [t.label for t in sorted(cls)]


class ProgramType(IntEnum):
    DEGREE = 0
    DIPLOMA = 1

    @property
    def label(self) -> str:
        return "Degree" if self is ProgramType.DEGREE else "Diploma"


@dataclass(frozen=True)
class Program:
    """A single program offering and its admission cutoffs.

    A ``None`` cutoff means "no explicit requirement for this prototype".
    ``preferred_track`` is informational only (not a hard gate).
    """

    code: str
    name: str
    college: str
    type: ProgramType
    gwa_min: Optional[float] = None
    math_min: Optional[float] = None
    english_min: Optional[float] = None
    umcet_min_tier: Optional[UMCETTier] = None
    preferred_track: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_degree(self) -> bool:
        return self.type is ProgramType.DEGREE


# --- grade input bounds (used by UI validation and rule engine) ---
GRADE_MIN = 75.0
GRADE_MAX = 100.0

# --- SHS strands offered in the picker (first is a neutral default) ---
SHS_TRACKS: tuple[str, ...] = (
    "STEM",
    "ICT (TVL)",
    "ABM",
    "HUMSS",
    "GAS",
    "Arts and Design",
    "Sports",
    "Other / Not listed",
)


# ---------------------------------------------------------------------------
# Catalog — keyed by college. Seed CCIS now; add other colleges later.
# Degree cutoffs per CCIS PDF: GWA >= 85, Math >= 85, English >= 83,
# UMCET >= Low Average. Diplomas: GWA >= 80, any UMCET tier accepted.
# ---------------------------------------------------------------------------
CCIS = "College of Computing and Information Sciences (CCIS)"

_CATALOG: dict[str, list[Program]] = {
    CCIS: [
        Program(
            code="BSCS",
            name="BS Computer Science",
            college=CCIS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=83.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            preferred_track=("STEM", "ICT (TVL)"),
        ),
        Program(
            code="BSIT",
            name="BS Information Technology",
            college=CCIS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=83.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            preferred_track=("STEM", "ICT (TVL)"),
        ),
        Program(
            code="BSIS",
            name="BS Information Systems",
            college=CCIS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=83.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            preferred_track=(),
        ),
        Program(
            code="DAD",
            name="Diploma in Application Development",
            college=CCIS,
            type=ProgramType.DIPLOMA,
            gwa_min=80.0,
            math_min=None,
            english_min=None,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,
            preferred_track=(),
        ),
        Program(
            code="DCNA",
            name="Diploma in Computer Network Administration",
            college=CCIS,
            type=ProgramType.DIPLOMA,
            gwa_min=80.0,
            math_min=None,
            english_min=None,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,
            preferred_track=(),
        ),
    ],
}


def all_colleges() -> list[str]:
    return list(_CATALOG.keys())


def programs_for(college: str = CCIS) -> list[Program]:
    """Return the programs offered by a college (CCIS by default)."""
    return list(_CATALOG.get(college, []))


def all_programs() -> list[Program]:
    """Flatten every program across every college in the catalog."""
    return [p for progs in _CATALOG.values() for p in progs]


def get_program(code: str) -> Program:
    for program in all_programs():
        if program.code == code:
            return program
    raise KeyError(f"No program with code {code!r}")
