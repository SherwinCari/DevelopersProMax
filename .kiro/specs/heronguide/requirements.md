# Requirements — HeronGuide (UMak CCIS Smart Admission Advisor)

## Overview

HeronGuide is a hackathon prototype that helps prospective University of Makati
(UMak) students, shifters, and transferees instantly determine which College of
Computing and Information Sciences (CCIS) programs they qualify for. It replaces
the friction of parsing static PDF requirements and the anxiety of enrollment-day
UMCET score reveals with a two-part system:

1. A **deterministic rule engine** that computes the eligibility verdict from a
   student's grades and UMCET tier (no guessing, no hallucination).
2. A **local LLM (Ollama / llama3.1:8b)** that only *explains* the verdict,
   routes disqualified applicants to realistic alternatives, and gives qualified
   applicants review recommendations plus a practice admission interview.

This is a prototype. Whether the final product runs online or offline, and which
LLM it ultimately uses, is a decision left to the school. The prototype must run
locally today via Ollama and be demo-safe for a live hackathon presentation.

## Goals

- Give an instant, accurate CCIS eligibility verdict from simple inputs.
- Explain *exactly* which requirement is missing when a student falls short.
- Always offer a realistic alternative path (diploma) instead of a dead end.
- Reward qualified students with next steps: what to review + a practice interview.
- Present a clean, UMak-themed experience that wins a hackathon.

## Non-Goals

- Not an official admissions decision system; it is advisory only.
- Not a production deployment; no accounts, database, or server hosting required.
- Does not replace the UMak entrance exam or official evaluation.
- Other UMak colleges are out of scope for the demo (data model stays extensible).

## Definitions

- **GWA** — General Weighted Average (senior high school), 75–100 scale.
- **UMCET** — UMak College Entrance Test, reported as a tier, not a number.
- **UMCET tiers (low → high):** Below Average, Low Average, Average, High Average, Excellent.
- **SHS Track / Strand** — e.g., STEM, ICT (TVL), ABM, HUMSS. Informational only.
- **Degree** — a 4-year Bachelor program (BS CS / BS IT / BS IS).
- **Diploma** — a shorter program (Application Development / Computer Network Administration).

## Confirmed Eligibility Rules

Rules are **data-driven** (defined in the program catalog) so admissions staff can
adjust thresholds without changing logic.

### Degrees — BS CS, BS IT, BS IS
- GWA ≥ 85
- Math ≥ 85
- English ≥ 83  *(per the official CCIS requirements PDF)*
- UMCET tier ≥ Low Average
- Preferred SHS track: STEM or ICT — **preferred, not required** (not a gate).

### Diplomas — Application Development, Computer Network Administration
- GWA ≥ 80
- No explicit Math/English subject cutoff for this prototype.
- UMCET tier: Below Average through Excellent all accepted.

### Fallback logic
- If a student fails any degree requirement, HeronGuide must surface the diploma
  alternative(s) they *do* qualify for.

---

## User Stories & Acceptance Criteria

### Story 1 — Pre-Screening by High School Grades
**As a** prospective UMak student
**I want to** enter my SHS track, GWA, Math, and English grades
**so that** I know which CCIS programs I may qualify for before I even take or
receive my UMCET result.

Acceptance Criteria:
1. WHEN the student enters GWA, Math, and English, THEN each input SHALL be
   constrained to the 75–100 range and reject out-of-range values.
2. WHEN a required cutoff is not met, THEN the system SHALL state the exact gap
   (e.g., "Math 84 is below the required 85").
3. WHEN the student enables "UMCET score not received yet", THEN the system SHALL
   evaluate grades only and mark the UMCET condition as *pending* rather than
   failing it.
4. The SHS track SHALL be captured and displayed but SHALL NOT by itself cause a
   program to be marked ineligible.

### Story 2 — Live Enrollment-Day Evaluation (UMCET Integration)
**As an** applicant standing in line on enrollment day
**I want to** select the UMCET tier I just received
**so that** my qualification status updates immediately.

Acceptance Criteria:
1. WHEN the student selects a UMCET tier AND all degree grade cutoffs are met AND
   the tier is ≥ Low Average, THEN the relevant degree(s) SHALL be marked
   **Fully Qualified**.
2. WHEN the UMCET tier is Below Average OR any grade falls below the degree
   baseline, THEN the system SHALL recommend the Diploma in Application
   Development and/or Diploma in Computer Network Administration where the
   student meets the 80 GWA baseline.
3. The verdict SHALL be produced by the deterministic rule engine, not the LLM.

### Story 3 — Empathetic Guidance & Alternative Pathways
**As an** applicant who does not qualify for a 4-year degree
**I want** the gap explained kindly with realistic alternatives
**so that** I don't abandon my application.

Acceptance Criteria:
1. WHEN a student is disqualified, THEN the explanation SHALL explicitly state the
   missing requirement(s).
2. The system SHALL always present at least one valid alternative (a diploma the
   student qualifies for) or a clear next administrative step.
3. The LLM SHALL only phrase the already-decided verdict; it SHALL NOT change
   whether a student is qualified.

### Story 4 — Next Steps for Qualified Students (Review + Practice Interview)
**As an** applicant who qualifies for a program
**I want** to know what to review and to practice an admission interview
**so that** I am prepared for the enrollment-day interview.

Acceptance Criteria:
1. WHEN a student is Fully Qualified for a program, THEN the system SHALL present
   program-specific review recommendations.
2. The system SHALL offer a short practice interview of 3–4 questions, one at a
   time, with brief encouraging feedback after each answer.
3. The student SHALL be able to skip or finish the practice interview at any time.

---

## Cross-Cutting / Non-Functional Requirements

1. **Determinism (Trust):** Eligibility verdicts SHALL come only from the rule
   engine. The LLM never decides qualification.
2. **Demo resilience:** Every LLM call SHALL have a timeout and a pre-written
   templated/question-bank fallback, so a slow or offline Ollama cannot break a
   live demo.
3. **Privacy:** All processing SHALL run locally; no student data leaves the
   machine in the prototype.
4. **Extensibility:** The program catalog SHALL be data-driven and structured so
   other UMak colleges can be added later without code changes.
5. **Branding:** The UI SHALL use the UMak visual identity (navy + gold, Heron
   branding) and present results as scannable status cards.
6. **Input validation:** Grade inputs SHALL be bounded to 75–100.
