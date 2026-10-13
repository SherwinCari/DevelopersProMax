"""Deterministic eligibility rule engine for HeronGuide.

This module is the single source of truth for admission verdicts. Every
numeric pass/fail decision happens here in plain Python. The LLM advisor
(``advisor.py``) only *explains* these results and never alters them — this
is the system's core trust property.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from data.programs import Program, UMCETTier, all_programs


class Status(Enum):
    """Verdict for a single program."""

    QUALIFIED = "Qualified"
    PENDING_UMCET = "Pending UMCET"   # grades pass; waiting on exam result
    NOT_QUALIFIED = "Not Yet Qualified"


@dataclass(frozen=True)
class Gap:
    """A single unmet requirement, phrased for direct display."""

    field: str      # "GWA" | "Math" | "English" | "UMCET"
    actual: str
    required: str
    message: str


@dataclass
class ProgramResult:
    program: Program
    status: Status
    gaps: list[Gap] = field(default_factory=list)
    preferred_track_met: bool = False


@dataclass
class StudentInput:
    """Everything the student provides. ``umcet_tier`` is None when the exam
    result has not been received yet (``umcet_received`` is False)."""

    gwa: float
    math: float
    english: float
    shs_track: str
    umcet_tier: Optional[UMCETTier] = None
    umcet_received: bool = False


def _grade_gap(field_name: str, actual: float, required: Optional[float]) -> Optional[Gap]:
    """Return a Gap if ``actual`` falls below ``required``; else None.

    A ``None`` requirement means the program has no cutoff for this field.
    """
    if required is None:
        return None
    if actual >= required:
        return None
    # Trim trailing .0 so messages read "84" not "84.0".
    a = f"{actual:g}"
    r = f"{required:g}"
    return Gap(
        field=field_name,
        actual=a,
        required=r,
        message=f"{field_name} {a} is below the required {r}",
    )


def _evaluate_program(student: StudentInput, program: Program) -> ProgramResult:
    gaps: list[Gap] = []

    for field_name, actual, required in (
        ("GWA", student.gwa, program.gwa_min),
        ("Math", student.math, program.math_min),
        ("English", student.english, program.english_min),
    ):
        gap = _grade_gap(field_name, actual, required)
        if gap is not None:
            gaps.append(gap)

    academics_pass = not gaps

    # UMCET handling
    umcet_pending = False
    if program.umcet_min_tier is not None:
        if not student.umcet_received or student.umcet_tier is None:
            umcet_pending = True
        elif student.umcet_tier < program.umcet_min_tier:
            gaps.append(
                Gap(
                    field="UMCET",
                    actual=student.umcet_tier.label,
                    required=program.umcet_min_tier.label,
                    message=(
                        f"UMCET rating '{student.umcet_tier.label}' is below the "
                        f"required '{program.umcet_min_tier.label}'"
                    ),
                )
            )

    # Resolve status: any recorded gap means not qualified; otherwise either
    # pending (grades pass, UMCET not yet received) or fully qualified.
    if gaps:
        status = Status.NOT_QUALIFIED
    elif academics_pass and umcet_pending:
        status = Status.PENDING_UMCET
    else:
        status = Status.QUALIFIED

    preferred_track_met = (
        not program.preferred_track
        or student.shs_track in program.preferred_track
    )

    return ProgramResult(
        program=program,
        status=status,
        gaps=gaps,
        preferred_track_met=preferred_track_met,
    )


def evaluate(student: StudentInput) -> list[ProgramResult]:
    """Evaluate the student against every program in the catalog."""
    return [_evaluate_program(student, p) for p in all_programs()]


def result_for(results: list[ProgramResult], code: str) -> ProgramResult:
    """Convenience lookup of a single program result by code."""
    for r in results:
        if r.program.code == code:
            return r
    raise KeyError(f"No result for program code {code!r}")


def alternatives(results: list[ProgramResult]) -> list[ProgramResult]:
    """Diploma programs the student qualifies for (or is pending on).

    Used to guarantee the UI always offers a realistic alternative path
    instead of a dead end.
    """
    return [
        r
        for r in results
        if not r.program.is_degree
        and r.status in (Status.QUALIFIED, Status.PENDING_UMCET)
    ]


def any_degree_attainable(results: list[ProgramResult]) -> bool:
    """True if at least one degree is Qualified or Pending UMCET."""
    return any(
        r.program.is_degree and r.status in (Status.QUALIFIED, Status.PENDING_UMCET)
        for r in results
    )
