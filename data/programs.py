"""Program catalog data model for HeronGuide.

Design goals
------------
* **Data-driven:** eligibility cutoffs live here, not in the rule engine, so
  admissions staff can adjust thresholds without touching logic.
* **Extensible:** the catalog is keyed by college -> list[Program]. Every UMak
  college is now seeded (36 programs, 16 colleges/institutes).
* **Deterministic:** UMCET tiers are an ordered enum so the rule engine can do
  a simple ``>=`` comparison.

Sources: UMak "College Admission Requirements" page, AY 2026-2027
(information as of August 7, 2026 9:53 AM) and ``kiro_hackathon_spec.md``.

Reading the source table
------------------------
* "UMak Examination Ratings (High - Low)" such as "Excellent - Average" is a
  range of accepted tiers, so ``umcet_min_tier`` is the LOWEST tier listed.
* "Any SHS Track" -> ``required_track = ()``; "STEM Track" ->
  ``required_track = ("STEM",)`` (hard gate); "Preferably / Preferred ..."
  -> ``preferred_track`` (informational only).
* ``X`` in the transferee/shifter or 2nd-courser column means the program does
  not accept them: ``shifter_notes`` / ``second_course_notes`` are ``None``.
* Transferee/shifter and 2nd-course requirements are kept as plain-text notes
  (nothing lost from the source), plus a parsed GWA cutoff where one is given.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class UMCETTier(IntEnum):
    """UMak entrance exam rating tiers, ordered low -> high.

    IntEnum lets the rule engine compare tiers directly (e.g.
    ``student_tier >= program.umcet_min_tier``).

    NOTE: INFERIOR, POOR and ABOVE_AVERAGE were added for the other colleges.
    The source page never lists the full scale, so the position of
    ABOVE_AVERAGE relative to HIGH_AVERAGE is an assumption -- please verify
    against the official UMCET rating table.
    """

    INFERIOR = 0
    POOR = 1
    BELOW_AVERAGE = 2
    LOW_AVERAGE = 3
    AVERAGE = 4
    ABOVE_AVERAGE = 5
    HIGH_AVERAGE = 6
    EXCELLENT = 7

    @property
    def label(self) -> str:
        return {
            UMCETTier.INFERIOR: "Inferior",
            UMCETTier.POOR: "Poor",
            UMCETTier.BELOW_AVERAGE: "Below Average",
            UMCETTier.LOW_AVERAGE: "Low Average",
            UMCETTier.AVERAGE: "Average",
            UMCETTier.ABOVE_AVERAGE: "Above Average",
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
    ASSOCIATE = 2

    @property
    def label(self) -> str:
        return {
            ProgramType.DEGREE: "Degree",
            ProgramType.DIPLOMA: "Diploma",
            ProgramType.ASSOCIATE: "Associate",
        }[self]


@dataclass(frozen=True)
class Program:
    """A single program offering and its admission cutoffs.

    A ``None`` cutoff means "no explicit requirement for this prototype".

    New-admission (incoming freshman) fields
    ----------------------------------------
    gwa_min              Minimum SHS GWA (%). For CBFS this is the NON-HSU value.
    gwa_min_hsu          Minimum GWA (%) for UMak Higher School (HSU) graduates.
                         ``None`` -> same as ``gwa_min``.
    gwa_min_non_academic Minimum GWA (%) for non-academic SHS tracks, when it
                         differs from ``gwa_min`` (BS Psychology).
    math_min / english_min / science_min
                         Minimum subject grade (%).
    all_subjects_min     Minimum grade in EVERY subject (BDRM).
    umcet_min_tier       Lowest accepted UMCET tier.
    required_track       Hard gate: student's SHS track must be in this tuple.
                         Empty tuple = any track.
    preferred_track      Informational only (not a hard gate).
    extra_requirements   Non-numeric items (skills test, portfolio, ...).

    Transferee / shifter / 2nd courser
    ----------------------------------
    shifter_gwa_pct / shifter_gwa_gp
                         Minimum GWA as a percentage, and as a grade point
                         (1.00 best ... 5.00); the source mixes both scales.
    shifter_notes        Verbatim requirements; ``None`` = not accepted.
    second_course_notes  Verbatim requirements; ``None`` = not accepted.
    """

    code: str
    name: str
    college: str
    type: ProgramType
    # --- new admission ---
    gwa_min: Optional[float] = None
    gwa_min_hsu: Optional[float] = None
    gwa_min_non_academic: Optional[float] = None
    math_min: Optional[float] = None
    english_min: Optional[float] = None
    science_min: Optional[float] = None
    all_subjects_min: Optional[float] = None
    umcet_min_tier: Optional[UMCETTier] = None
    required_track: tuple[str, ...] = field(default_factory=tuple)
    preferred_track: tuple[str, ...] = field(default_factory=tuple)
    extra_requirements: tuple[str, ...] = field(default_factory=tuple)
    # --- transferee / shifter ---
    shifter_gwa_pct: Optional[float] = None
    shifter_gwa_gp: Optional[float] = None
    shifter_notes: Optional[tuple[str, ...]] = None
    # --- 2nd courser ---
    second_course_notes: Optional[tuple[str, ...]] = None

    @property
    def is_degree(self) -> bool:
        return self.type is ProgramType.DEGREE

    @property
    def accepts_shifters(self) -> bool:
        return self.shifter_notes is not None

    @property
    def accepts_second_course(self) -> bool:
        return self.second_course_notes is not None

    @property
    def any_track(self) -> bool:
        return not self.required_track

    def gwa_min_for(self, *, hsu_graduate: bool = False,
                    academic_track: bool = True) -> Optional[float]:
        """Resolve the GWA cutoff for a given applicant profile."""
        if hsu_graduate and self.gwa_min_hsu is not None:
            return self.gwa_min_hsu
        if not academic_track and self.gwa_min_non_academic is not None:
            return self.gwa_min_non_academic
        return self.gwa_min


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

# Academic-track strands (BS Psychology uses a lower GWA bar for these).
ACADEMIC_TRACKS: tuple[str, ...] = ("STEM", "ABM", "HUMSS", "GAS")

SOURCE_UPDATED = "August 7, 2026 9:53 AM"
ACADEMIC_YEAR = "2026-2027"

# ---------------------------------------------------------------------------
# Colleges / institutes (full names exactly as on the admissions page)
# ---------------------------------------------------------------------------
IAD = "Institute of Arts and Design (IAD)"
CCIS = "College of Computing and Information Sciences (CCIS)"
CGPP = "College of Governance & Public Policy (CGPP)"
IIHS = "Institute of Imaging Health Science (IIHS)"
IOP = "Institute of Pharmacy (IOP)"
ION = "Institute of Nursing (IoN)"
CHK = "College of Human Kinetics (CHK)"
IOPSY = "Institute of Psychology (IOPSY)"
CCSE = "College of Construction Sciences and Engineering (CCSE)"
CITE = "College of Innovative Teacher Education (CITE)"
CET = "College of Engineering Technology (CET)"
CTHM = "College of Tourism & Hospitality Management (CTHM)"
CBFS = "College of Business and Financial Science (CBFS)"
IOA = "Institute of Accountancy (IOA)"
ISW = "Institute of Social Work"
IDEM = "Institute for Disaster and Emergency Management"

# ---------------------------------------------------------------------------
# Reusable verbatim requirement notes
# ---------------------------------------------------------------------------
_STANDARD_RECORD = ("No Failing Grade", "No Unofficially Dropped", "No Incomplete")
_NO_UPPER_YEARS = ("No Incoming Third or Fourth Year",)
_TOR = "TOR Evaluation/Validation"

_CCIS_SHIFT = (
    "GWA 2.00 (85% to 87%)",
    "No Failing Grade, Unofficially Dropped, Incomplete Grade in IT or "
    "Computing Courses (Subject for approval - Max of 3)",
)
_CCIS_2ND = (_TOR, "GWA 2.00 (85% to 87%) or higher")

_CBFS_LOWER_SHIFT = (
    "GWA: 2.50 (80%)",
    "NO Grade Lower than 2.50 all semester",
    "NO Failing Grade",
    "NO Unofficially Dropped",
    "NO Incomplete",
    "Letter of Approval from the Former College",
    "NO Incoming for 3rd year or 4th Year",
)
_CBFS_UPPER_SHIFT = (
    "GWA 2.25 (82% to 84%)",
    *_STANDARD_RECORD,
    *_NO_UPPER_YEARS,
)
_CBFS_TOR = "TOR Evaluation/Validation should come from the registrar"
_CBFS_2ND = (_CBFS_TOR, "GWA 2.00 (85% to 87%) or higher", *_STANDARD_RECORD)

_CITE_2ND = ("Requirements for TCP Only",)

# ---------------------------------------------------------------------------
# Catalog -- keyed by college.
# ---------------------------------------------------------------------------
_CATALOG: dict[str, list[Program]] = {
    # ------------------------------------------------------------------ IAD
    IAD: [
        Program(
            code="BMMA-ANIM",
            name="Bachelor in Multimedia Arts (Animation Track)",
            college=IAD,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            extra_requirements=("Skills Test", "Portfolio"),
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA 2.0",
                "No failing grade",
                "Letter of Intent/Application",
                "Skills Test",
                "Interview",
                "Evaluation of BMMA Program Director",
            ),
            second_course_notes=(
                "T.O.R",
                "Letter of Intent/Application",
                "Portfolio/Filmograph",
                "Interview",
            ),
        ),
        Program(
            code="BMMA-FILM",
            name="Bachelor in Multimedia Arts (Film Production Track)",
            college=IAD,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            extra_requirements=("Skills Test", "Portfolio"),
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA 2.0",
                "No failing grade",
                "Letter of Intent/Application",
                "Skills Test",
                "Interview",
                "Evaluation of BMMA Program Director",
            ),
            second_course_notes=(
                "T.O.R",
                "Letter of Intent/Application",
                "Portfolio/Filmograph",
                "Interview",
            ),
        ),
        Program(
            code="BACOMM",
            name="BA Communication",
            college=IAD,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            shifter_gwa_gp=2.5,
            shifter_notes=(
                "GWA 2.5 or better",
                "Letter of Intent/Application",
                "Interview with BA Comm. Program Director",
            ),
            second_course_notes=(
                "T.O.R",
                "Letter of Intent/Application",
                "Interview with BA Comm. Program Director",
            ),
        ),
    ],
    # ----------------------------------------------------------------- CCIS
    CCIS: [
        Program(
            code="BSCS",
            name="BS Computer Science (Application Development Elective Track)",
            college=CCIS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=83.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            preferred_track=("STEM", "ICT (TVL)"),
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=_CCIS_SHIFT,
            second_course_notes=_CCIS_2ND,
        ),
        Program(
            code="BSIT",
            name="BS Information Technology (Information and Network Security Elective Track)",
            college=CCIS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=83.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            preferred_track=("STEM", "ICT (TVL)"),
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=_CCIS_SHIFT,
            second_course_notes=_CCIS_2ND,
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
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=_CCIS_SHIFT,
            second_course_notes=_CCIS_2ND,
        ),
        Program(
            code="DAD",
            name="Diploma in Application Development",
            college=CCIS,
            type=ProgramType.DIPLOMA,
            gwa_min=80.0,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,
        ),
        Program(
            code="DCNA",
            name="Diploma in Computer Network Administration",
            college=CCIS,
            type=ProgramType.DIPLOMA,
            gwa_min=80.0,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,
        ),
    ],
    # ----------------------------------------------------------------- CGPP
    CGPP: [
        Program(
            code="ABPOLSCI",
            name="Bachelor of Arts in Political Science",
            college=CGPP,
            type=ProgramType.DEGREE,
            gwa_min=80.0,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,
        ),
    ],
    # ----------------------------------------------------------------- IIHS
    IIHS: [
        Program(
            code="BSRT",
            name="BS Radiologic Technology",
            college=IIHS,
            type=ProgramType.DEGREE,
            gwa_min=90.0,
            math_min=88.0,
            english_min=88.0,
            science_min=88.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            required_track=("STEM",),
            shifter_gwa_pct=95.0,
            shifter_notes=(
                "GWA: 95% or higher",
                "No grade lower than 92% IN all semesters",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
        ),
    ],
    # ------------------------------------------------------------------ IOP
    IOP: [
        Program(
            code="BSPHARM",
            name="BS Pharmacy",
            college=IOP,
            type=ProgramType.DEGREE,
            gwa_min=90.0,
            math_min=88.0,
            english_min=88.0,
            science_min=88.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            required_track=("STEM",),
            shifter_gwa_pct=88.0,
            shifter_gwa_gp=1.75,
            shifter_notes=(
                "GWA: 1.75 (88% to 90%) or higher",
                "No grade lower than 1.75 (88% to 90%), all semesters",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA: 1.75 (88% to 90%) or higher",
                "No grade lower than 1.75 (88% to 90%), all semesters",
                *_STANDARD_RECORD,
            ),
        ),
    ],
    # ------------------------------------------------------------------ ION
    ION: [
        Program(
            code="BSN",
            name="BS Nursing",
            college=ION,
            type=ProgramType.DEGREE,
            gwa_min=92.0,
            math_min=90.0,
            english_min=90.0,
            science_min=90.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            required_track=("STEM",),
        ),
    ],
    # ------------------------------------------------------------------ CHK
    CHK: [
        Program(
            code="BSESS",
            name="BS Exercise and Sports Science",
            college=CHK,
            type=ProgramType.DEGREE,
            gwa_min=82.0,
            math_min=82.0,
            english_min=82.0,
            science_min=82.0,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,  # source: "Average - Below Average"
            shifter_gwa_pct=82.0,
            shifter_gwa_gp=2.25,
            shifter_notes=(
                "GWA 2.25 (82% to 84%)",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA 2.25 (82% to 84%)",
                *_STANDARD_RECORD,
            ),
        ),
    ],
    # ---------------------------------------------------------------- IOPSY
    IOPSY: [
        Program(
            code="BSPSY",
            name="BS Psychology",
            college=IOPSY,
            type=ProgramType.DEGREE,
            gwa_min=85.0,               # Academic track
            gwa_min_non_academic=88.0,  # Non-academic track
            math_min=85.0,
            english_min=85.0,
            science_min=85.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            extra_requirements=("Psychological Test Assessment",),
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA: 2.00 (85% to 87%) or higher",
                "Psychological Test Assessment",
                "No grade lower than 2.00 (85% to 87%), all semesters",
                "No Failing Grade, No Unofficially Dropped, No Incomplete",
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA: 2.00 (85% to 87%) or higher",
                "No grade lower than 2.00 (85% to 87%), all semesters",
                "No Failing Grade, No Unofficially Dropped, No Incomplete",
                "Psychological Test Assessment",
            ),
        ),
    ],
    # ----------------------------------------------------------------- CCSE
    CCSE: [
        Program(
            code="BSCE",
            name="BS Civil Engineering (BSCE) 4-yrs",
            college=CCSE,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=85.0,
            science_min=85.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            required_track=("STEM",),
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA 2.00 (85% to 87%)",
                "No Grades below 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA: 2.00 (85% to 87%) or higher",
                "No grade lower than 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
            ),
        ),
    ],
    # ----------------------------------------------------------------- CITE
    CITE: [
        Program(
            code="BEED",
            name="Bachelor in Elementary Education (BEED)",
            college=CITE,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=85.0,
            science_min=85.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA 2.00 (85% to 87%)",
                "No Grades below 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=_CITE_2ND,
        ),
        Program(
            code="BSE",
            name="Bachelor in Secondary Education (BSE) Major in: English, Mathematics, Social Studies",
            college=CITE,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            math_min=85.0,
            english_min=85.0,
            science_min=85.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA 2.00 (85% to 87%)",
                "No Grades below 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=_CITE_2ND,
        ),
    ],
    # ------------------------------------------------------------------ CET
    CET: [
        Program(
            code="BET-ELECT",
            name="Bachelor of Engineering Technology Major in Electrical Technology",
            college=CET,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=("GWA 2.00 (85%)", *_STANDARD_RECORD, *_NO_UPPER_YEARS),
            second_course_notes=(_TOR, "GWA 2.00 (85%)", *_STANDARD_RECORD),
        ),
        Program(
            code="BET-ELEX",
            name="Bachelor of Engineering Technology Major in Electronics Technology",
            college=CET,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            umcet_min_tier=UMCETTier.BELOW_AVERAGE,
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=("GWA 2.00 (85%)", *_STANDARD_RECORD, *_NO_UPPER_YEARS),
            second_course_notes=(_TOR, "GWA 2.00 (85%)", *_STANDARD_RECORD),
        ),
        Program(
            code="DIFT",
            name="Diploma in Industrial Facilities Technology",
            college=CET,
            type=ProgramType.DIPLOMA,
            gwa_min=75.0,
            umcet_min_tier=UMCETTier.INFERIOR,
            shifter_notes=_STANDARD_RECORD,
            second_course_notes=(
                _TOR,
                "No Failing Grade, No Unofficially Dropped and Incomplete",
            ),
        ),
        Program(
            code="DIFT-SM",
            name="Diploma in Industrial Facilities Technology Major in Service Mechanics",
            college=CET,
            type=ProgramType.DIPLOMA,
            gwa_min=75.0,
            umcet_min_tier=UMCETTier.INFERIOR,
            shifter_notes=_STANDARD_RECORD,
            second_course_notes=(
                _TOR,
                "No Failing Grade, No Unofficially Dropped and Incomplete",
            ),
        ),
    ],
    # ----------------------------------------------------------------- CTHM
    CTHM: [
        Program(
            code="BSTM",
            name="BS Tourism Management",
            college=CTHM,
            type=ProgramType.DEGREE,
            gwa_min=87.0,
            math_min=88.0,
            english_min=90.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            preferred_track=("ABM", "STEM", "HUMSS"),
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA 2.00 (85% to 87%)",
                "No grades lower than 90% in English and no grades lower than 88% in Mathematics",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA 2.00 (85% to 87%)",
                "No grades lower than 90% in English and no grades lower than 88% in Mathematics",
                *_STANDARD_RECORD,
            ),
        ),
        Program(
            code="BSHM",
            name="BS Hospitality Management",
            college=CTHM,
            type=ProgramType.DEGREE,
            gwa_min=87.0,
            math_min=88.0,
            english_min=90.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            preferred_track=("ABM", "STEM", "HUMSS"),
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA 2.00 (85% to 87%)",
                "No grades lower than 90% in English and no grades lower than 88% in Mathematics",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA 2.00 (85% to 87%)",
                "No grades lower than 90% in English and no grades lower than 88% in Mathematics",
                *_STANDARD_RECORD,
            ),
        ),
        Program(
            code="AHM",
            name="Associate in Hospitality Management",
            college=CTHM,
            type=ProgramType.ASSOCIATE,
            gwa_min=85.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            shifter_gwa_pct=79.0,
            shifter_gwa_gp=2.5,
            shifter_notes=("GWA 2.50 (79% to 81%)", *_STANDARD_RECORD),
            second_course_notes=(_TOR, "GWA 2.50 (79% to 81%)", *_STANDARD_RECORD),
        ),
    ],
    # ----------------------------------------------------------------- CBFS
    # gwa_min = NON-HSU graduates; gwa_min_hsu = UMak Higher School graduates.
    CBFS: [
        Program(
            code="BSBA-BPM",
            name="BS Business Administration Major in Building and Property Management",
            college=CBFS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            gwa_min_hsu=80.0,
            umcet_min_tier=UMCETTier.POOR,
            shifter_gwa_pct=80.0,
            shifter_gwa_gp=2.5,
            shifter_notes=_CBFS_LOWER_SHIFT,
            second_course_notes=_CBFS_2ND[:2],
        ),
        Program(
            code="BSBA-SM",
            name="BS Business Administration Major in Supply Management",
            college=CBFS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            gwa_min_hsu=80.0,
            umcet_min_tier=UMCETTier.POOR,
            shifter_gwa_pct=80.0,
            shifter_gwa_gp=2.5,
            shifter_notes=_CBFS_LOWER_SHIFT,
            second_course_notes=_CBFS_2ND[:2],
        ),
        Program(
            code="BSBA-HRMD",
            name="BS Business Administration Major in Human Resource Management and Development",
            college=CBFS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            gwa_min_hsu=80.0,
            umcet_min_tier=UMCETTier.POOR,
            shifter_gwa_pct=80.0,
            shifter_gwa_gp=2.5,
            shifter_notes=_CBFS_LOWER_SHIFT,
            second_course_notes=_CBFS_2ND,
        ),
        Program(
            code="BSOA",
            name="BS Office Administration",
            college=CBFS,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            gwa_min_hsu=80.0,
            umcet_min_tier=UMCETTier.POOR,
            shifter_gwa_pct=80.0,
            shifter_gwa_gp=2.5,
            shifter_notes=_CBFS_LOWER_SHIFT,
            second_course_notes=_CBFS_2ND,
        ),
        Program(
            code="BSEM",
            name="BS Entrepreneurial Management",
            college=CBFS,
            type=ProgramType.DEGREE,
            gwa_min=88.0,
            gwa_min_hsu=83.0,
            umcet_min_tier=UMCETTier.POOR,
            shifter_gwa_pct=82.0,
            shifter_gwa_gp=2.25,
            shifter_notes=_CBFS_UPPER_SHIFT,
            second_course_notes=_CBFS_2ND,
        ),
        Program(
            code="BSBA-MM",
            name="BS Business Administration Major in Marketing Management",
            college=CBFS,
            type=ProgramType.DEGREE,
            gwa_min=88.0,
            gwa_min_hsu=83.0,
            umcet_min_tier=UMCETTier.POOR,
            shifter_gwa_pct=82.0,
            shifter_gwa_gp=2.25,
            shifter_notes=_CBFS_UPPER_SHIFT,
            second_course_notes=_CBFS_2ND,
        ),
        Program(
            code="BSBA-FM",
            name="BS Business Administration Major in Financial Management",
            college=CBFS,
            type=ProgramType.DEGREE,
            gwa_min=88.0,
            gwa_min_hsu=83.0,
            umcet_min_tier=UMCETTier.POOR,
            shifter_gwa_pct=82.0,
            shifter_gwa_gp=2.25,
            shifter_notes=_CBFS_UPPER_SHIFT,
            second_course_notes=_CBFS_2ND,
        ),
    ],
    # ------------------------------------------------------------------ IOA
    IOA: [
        Program(
            code="BSMA",
            name="BS Management Accounting (BSMA)",
            college=IOA,
            type=ProgramType.DEGREE,
            gwa_min=90.0,
            math_min=85.0,
            english_min=85.0,
            science_min=85.0,
            umcet_min_tier=UMCETTier.HIGH_AVERAGE,
            shifter_gwa_pct=91.0,
            shifter_gwa_gp=1.5,
            shifter_notes=(
                "GWA: 1.50 (91% to 93%) or higher",
                "Same requirements as new admission",
                "No grade lower than 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA: 1.50 (91% to 93%) or higher",
                "No grade lower than 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
            ),
        ),
        Program(
            code="BSA",
            name="BS Accountancy",
            college=IOA,
            type=ProgramType.DEGREE,
            gwa_min=90.0,
            math_min=85.0,
            english_min=85.0,
            science_min=85.0,
            umcet_min_tier=UMCETTier.ABOVE_AVERAGE,
            shifter_gwa_pct=91.0,
            shifter_gwa_gp=1.5,
            shifter_notes=(
                "GWA: 1.50 (91% to 93%) or higher",
                "Same requirements as new admission",
                "No grade lower than 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
                *_NO_UPPER_YEARS,
            ),
            second_course_notes=(
                _TOR,
                "GWA: 1.50 (91% to 93%) or higher",
                "No grade lower than 2.00 (85% to 87%), all semesters",
                *_STANDARD_RECORD,
            ),
        ),
    ],
    # ------------------------------------------------------------------ ISW
    ISW: [
        Program(
            code="BSSW",
            name="BS Social Work (BSSW)",
            college=ISW,
            type=ProgramType.DEGREE,
            gwa_min=85.0,
            umcet_min_tier=UMCETTier.INFERIOR,
            shifter_gwa_pct=85.0,
            shifter_gwa_gp=2.0,
            shifter_notes=(
                "GWA: 2.00 (85%) or higher",
                "Same requirements as new admission",
                *_STANDARD_RECORD,
            ),
            second_course_notes=(
                _TOR,
                "GWA: 2.00 (85%) or higher",
                *_STANDARD_RECORD,
            ),
        ),
    ],
    # ----------------------------------------------------------------- IDEM
    IDEM: [
        Program(
            code="BDRM",
            name="Bachelor of Disaster Risk Management",
            college=IDEM,
            type=ProgramType.DEGREE,
            gwa_min=80.0,
            all_subjects_min=80.0,
            umcet_min_tier=UMCETTier.LOW_AVERAGE,
            shifter_gwa_gp=2.30,
            shifter_notes=("GWA: 2.30 or higher", *_STANDARD_RECORD),
            second_course_notes=(_TOR, "GWA of 2.30 or higher", *_STANDARD_RECORD),
        ),
        Program(
            code="DEMS",
            name="Diploma in Emergency Medical Services Leading to BS Paramedicine",
            college=IDEM,
            type=ProgramType.DIPLOMA,
            gwa_min=83.0,
            math_min=85.0,
            science_min=85.0,
            umcet_min_tier=UMCETTier.AVERAGE,
            required_track=("STEM",),
            shifter_gwa_pct=83.0,
            shifter_notes=(
                "GWA: 83 or higher",
                "No grades lower than 85% in Science and Math",
                *_STANDARD_RECORD,
            ),
            second_course_notes=(_TOR, "GWA: 83% or higher", *_STANDARD_RECORD),
        ),
    ],
}


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------
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


def programs_by_type(program_type: ProgramType) -> list[Program]:
    return [p for p in all_programs() if p.type is program_type]