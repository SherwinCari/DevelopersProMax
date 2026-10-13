# Design — HeronGuide (UMak CCIS Smart Admission Advisor)

## 1. Chosen Stack & Rationale

**Streamlit**, themed with custom CSS, talking to a **local Ollama** runtime
(`llama3.1:8b`).

Why Streamlit for a hackathon:
- Already installed in the project `venv` (zero infrastructure risk).
- Single language (Python), no Node/CORS/two-server juggling — demo-safe.
- Fastest reliable path to a finished, polished build within time limits.
- Uniqueness comes from the idea and polish — the deterministic-rules-vs-LLM
  split, empathetic alternative-path routing, the review + practice-interview
  flow, the offline/privacy story, and a sharp UMak-themed UI — not from the
  framework.

Verified environment: Python 3.14.6 venv with streamlit 1.65.0, ollama 0.6.3,
pydantic 2.13.5, pandas, numpy, pytest. Ollama serves `llama3.1:8b` at
`localhost:11434`.

## 2. Architecture

```
Streamlit UI (UMak-themed: navy + gold, Heron branding)
   │  inputs: SHS track, GWA, Math, English, UMCET tier (+ "not received yet" toggle)
   ▼
Rule Engine (pure Python, deterministic)
   │     → Verdict per program: Qualified / Not Yet Qualified + exact gaps
   │
   ├──(disqualified)──► LLM Advisor: empathetic explanation + diploma alternatives
   │
   └──(qualified)─────► LLM Advisor: review recommendations + practice interview
   │
   ▼  (every LLM call: timeout + templated / question-bank fallback)
Results UI: themed status cards, exact gap callouts, alternatives, AI guidance panel
```

### Core design principle — rules decide, the LLM only phrases
The rule engine computes the verdict and the exact gaps. The LLM receives that
*already-decided* result and writes human-friendly prose around it. It can never
flip a verdict. This is the system's main trust property and the key talking
point for judges ("the AI never guesses whether you got in").

## 3. Project Structure

```
kiro2.1/
  app.py                     # Streamlit entry, UI flow, session state
  rules.py                   # deterministic rule engine
  advisor.py                 # Ollama calls: explain, recommend_review, interview + fallbacks
  ui_theme.py                # UMak CSS, header, result cards, footer
  data/
    programs.py              # program catalog (CCIS seeded, extensible)
  .streamlit/config.toml     # Streamlit theme (UMak palette)
  tests/                     # pytest: catalog, rules, mocked advisor, interview flow
  requirements.txt           # pinned deps
  README.md                  # setup + pitch tagline
```

## 4. Data Model (`data/programs.py`)

- `UMCETTier(IntEnum)` — BELOW_AVERAGE=0 … EXCELLENT=4, with `.label`,
  `.from_label()`, `.ordered_labels()`. IntEnum enables a direct `>=` comparison.
- `ProgramType(IntEnum)` — DEGREE / DIPLOMA.
- `Program` (frozen dataclass) — `code, name, college, type, gwa_min, math_min,
  english_min, umcet_min_tier, preferred_track`. `None` cutoff = no requirement.
- Catalog keyed by **college → list[Program]**. CCIS seeded; other colleges
  pluggable later with no logic changes.
- Constants: `GRADE_MIN=75`, `GRADE_MAX=100`, `SHS_TRACKS`.

Seeded CCIS data:

| Code | Program | Type | GWA | Math | English | UMCET min |
|------|---------|------|-----|------|---------|-----------|
| BSCS | BS Computer Science | Degree | 85 | 85 | 83 | Low Average |
| BSIT | BS Information Technology | Degree | 85 | 85 | 83 | Low Average |
| BSIS | BS Information Systems | Degree | 85 | 85 | 83 | Low Average |
| DAD  | Diploma in Application Development | Diploma | 80 | — | — | Below Average |
| DCNA | Diploma in Computer Network Administration | Diploma | 80 | — | — | Below Average |

## 5. Rule Engine (`rules.py`)

### Inputs
```python
@dataclass
class StudentInput:
    gwa: float
    math: float
    english: float
    shs_track: str
    umcet_tier: UMCETTier | None   # None when "not received yet"
    umcet_received: bool
```

### Outputs
```python
class Status(Enum):
    QUALIFIED      # meets all requirements
    PENDING_UMCET  # grades qualify; waiting on UMCET (pre-screening mode)
    NOT_QUALIFIED  # at least one requirement failed

@dataclass
class Gap:
    field: str          # "GWA" | "Math" | "English" | "UMCET"
    actual: str
    required: str
    message: str        # e.g. "Math 84 is below the required 85"

@dataclass
class ProgramResult:
    program: Program
    status: Status
    gaps: list[Gap]              # empty when QUALIFIED
    preferred_track_met: bool    # informational only
```

### `evaluate(student) -> list[ProgramResult]`
For each program:
1. Check GWA / Math / English against cutoffs; record a `Gap` for each miss.
2. Check UMCET:
   - If `umcet_received` is False → UMCET condition is *pending* (no gap).
   - Else compare `student.umcet_tier >= program.umcet_min_tier`; miss → `Gap`.
3. Resolve status:
   - Any academic gap → `NOT_QUALIFIED`.
   - Academics pass but UMCET pending → `PENDING_UMCET`.
   - Academics pass and UMCET meets floor → `QUALIFIED`.
4. SHS track never produces a gap; it only sets `preferred_track_met`.

### `alternatives(results) -> list[ProgramResult]`
Returns the diploma results the student is `QUALIFIED` / `PENDING_UMCET` for,
used when no degree is attainable, satisfying the "never a dead end" rule.

All numeric comparisons live here; the LLM is never consulted for a verdict.

## 6. LLM Advisor (`advisor.py`)

Uses the `ollama` Python client against `llama3.1:8b`. Each function takes the
already-decided verdict and returns prose. All calls are wrapped with a timeout
and a deterministic fallback so the demo never stalls.

- `explain(student, results) -> str`
  Empathetic summary of the verdict. For disqualified students, names the exact
  missing requirement and encourages the diploma alternative. Prompt is
  constrained: "Do not change the decision; only explain it kindly."
- `recommend_review(student, program) -> str`
  Program-specific review topics + motivation for a qualified student
  (e.g., BS CS → logic, basic programming, math fundamentals, "why CS").
- Practice interview helpers:
  - `interview_question(program, index) -> str` — one question at a time.
  - `interview_feedback(program, question, answer) -> str` — brief, encouraging.
  - A pre-written **question bank** per program is the fallback.

### Resilience pattern
```python
def _with_fallback(call, fallback, timeout=20):
    try:
        return run_with_timeout(call, timeout)   # thread + join(timeout)
    except (TimeoutError, ConnectionError, Exception):
        return fallback
```
If Ollama is slow, unreachable, or errors, the user still sees good content.

## 7. UI Flow (`app.py` + `ui_theme.py`)

1. **Header** — branded banner with privacy/offline/local-AI badges.
2. **Input form** — SHS track dropdown; GWA/Math/English number inputs
   (75–100, validated); "UMCET not received yet" toggle; when off, a UMCET tier
   selector appears. Example-student quick-fill buttons for the demo.
3. **Results** — one themed status card per CCIS program:
   - 🟢 green = Qualified, 🟡 amber = Not Yet / pending with the exact gap,
     listed plainly.
   - Alternatives section when no degree is attainable.
4. **AI guidance panel** — spinner while generating; shows `explain(...)`.
5. **Qualified path** — review recommendations + a session-managed practice
   interview (3–4 questions via `st.session_state`, with skip/finish).

### State
`st.session_state` holds the current `StudentInput`, computed results, and the
interview progress (current question index, collected answers, feedback).

## 8. Theming

Defined in `.streamlit/config.toml` + CSS in `ui_theme.py`:
- Navy `#0B1F4D` text/primary, gold `#F2A900` accent, soft `#F3F6FB` panels.
- Status colors: green `#1E8E3E`, amber `#C77700`, red `#C5221F`.
- Gradient header, pill badges, left-accent result cards, advisor panel.

## 9. Testing Strategy

- **Catalog** (`tests/test_programs.py`): fields present, tier ordering, cutoffs.
- **Rules** (`tests/test_rules.py`): fully qualified; fail-by-1% exact gap;
  Below-Average UMCET → diploma fallback; UMCET-not-received → PENDING; SHS track
  non-gating. Written test-first.
- **Advisor** (`tests/test_advisor.py`): Ollama mocked — verify prompts are
  constrained and the fallback triggers on timeout/error.
- Manual: live run with `llama3.1:8b` on and off.

## 10. Demo Story Arcs

- **Qualified:** verdict → congrats explanation → what to review → practice interview.
- **Disqualified:** verdict → empathetic explanation → diploma alternatives → next steps.
