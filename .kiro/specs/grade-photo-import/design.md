# Design — Grade Photo Import (HeronGuide feature)

## 1. Where it fits

This feature adds a **vision extraction** step *in front of* the existing
eligibility form on `views/home.py`. It changes nothing about how verdicts are
produced: `rules.evaluate()` still decides eligibility, and `advisor.explain_ex()`
still phrases the result. The vision model is used only to turn an uploaded image
into draft values for the form.

```
Home tab
┌──────────────────────────────┬───────────────────────────────┐
│  Check your eligibility       │  Your results                 │
│  ┌─────────────────────────┐ │  (verdict cards + AI advisor) │
│  │ Insert grade photo for  │ │                               │
│  │ faster result  [upload] │ │                               │
│  └─────────────────────────┘ │                               │
│   GWA | Math | English | ...  │                               │
│   [Evaluate eligibility]      │                               │
└──────────────────────────────┴───────────────────────────────┘
          │
          ▼
  vision.extract_grades(image_bytes)  →  GradeExtraction (editable draft)
          │  (fills st.session_state in_gwa/in_math/in_eng/in_track)
          ▼
  existing manual flow: validate → StudentInput → rules.evaluate → advisor
```

## 2. Model constraint & choice

`llama3.1:8b` is text-only. Image reading needs a **vision model**. The design
centralizes this so it is swappable:

- `VISION_MODEL` env override, default `"llava"`.
- Suggested options: `llava` (lightest common choice), `llama3.2-vision`
  (stronger OCR, larger), `minicpm-v`, `moondream`.
- Prerequisite command for the demo machine: `ollama pull llava`.

If the configured vision model is not present, the feature detects it and shows
the manual-entry notice instead of failing.

## 3. New module: `vision.py`

Mirrors the structure and resilience pattern of `advisor.py` (shared client,
timeout harness, graceful fallback).

```python
from dataclasses import dataclass

VISION_MODEL = os.environ.get("VISION_MODEL", "llava")

@dataclass
class GradeExtraction:
    gwa: float | None
    math: float | None
    english: float | None
    shs_track: str | None
    raw_text: str          # model's raw reading, for transparency/debug
    notes: str             # short human-readable summary of what was/wasn't found
    ok: bool               # True if at least one usable value was extracted

def vision_available() -> bool: ...
    # like advisor.ollama_available() but checks for VISION_MODEL

def extract_grades(image_bytes: bytes, timeout: float = 90.0) -> GradeExtraction: ...
    # calls the vision model with a strict JSON-only prompt; parses + validates
```

### Prompt strategy (strict, parseable)
- System: "You read grades from an image of a student's report card. Return ONLY
  JSON. Do not guess; use null when a value is not clearly visible."
- User: image + instruction to return
  `{"gwa": number|null, "math": number|null, "english": number|null, "shs_track": string|null}`.
- Parsing: extract the first JSON object from the response (robust to extra
  prose); coerce numbers; discard anything outside 75–100 (set to null + note).
- `temperature` low (e.g. 0.1) for deterministic reading.

### Image passing
The `ollama` Python client accepts image bytes/paths via the `images` field on a
chat message. The uploaded file's bytes are passed directly; nothing is written
to disk (privacy). A size guard rejects files > 10 MB.

### Resilience
Reuse the timeout/thread harness pattern from `advisor.py`. On timeout, missing
model, parse failure, or any exception → return
`GradeExtraction(ok=False, notes="...manual entry...")`. The UI then keeps the
manual form fully usable.

## 4. UI changes in `views/home.py`

Inside the existing left-column `st.container(border=True)` "Check your
eligibility" block, add a photo panel **above** the grade inputs:

```
#### Check your eligibility
┌ Insert grade photo for faster result ───────────────┐
│ st.file_uploader(type=["png","jpg","jpeg","webp"])  │
│ [Read grades from photo]  (button, primary=False)   │
│ small caption: local & private; you can edit results│
└─────────────────────────────────────────────────────┘
GWA | Math | English | SHS strand | UMCET ...
[Evaluate eligibility]
```

Behavior:
1. If `vision.vision_available()` is False → render a muted notice: "Photo
   reading needs a local vision model (e.g. `llava`). Enter grades manually for
   now." The uploader may still show but the read button is disabled.
2. On **Read grades from photo** click with an uploaded file:
   - Validate it's an image and within the size limit.
   - `with st.spinner("Reading your grades…")`: call `extract_grades(bytes)`.
   - On success: write extracted values into `st.session_state` keys the form
     already uses (`in_gwa`, `in_math`, `in_eng`, `in_track`), then `st.rerun()`
     so the inputs show the draft. Show an `st.success`/`st.info` listing which
     fields were auto-filled and a reminder to verify.
   - On `ok=False`: `st.warning(extraction.notes)` and leave the form for manual
     entry.
3. The existing **Evaluate eligibility** button is unchanged; evaluation still
   runs only on explicit click, through the same validation + rule engine.

State keys reused: `in_gwa`, `in_math`, `in_eng`, `in_track` (so the extraction
simply seeds the same widgets manual entry uses). A new transient key
`hg_vision_notes` can hold the last extraction summary for display.

## 5. Theming

Add a light-weight themed sub-panel style (reuse existing `ui_theme` card/banner
helpers where possible). The panel uses the UMak accent for the heading and a
dashed drop-zone look consistent with the current card styling.

## 6. Testing Strategy

- `tests/test_vision.py` (no live model needed):
  - JSON parsing: well-formed JSON → correct `GradeExtraction`.
  - Robust parsing: JSON embedded in extra prose still parsed.
  - Out-of-range values (e.g. 150) → dropped to null with a note.
  - Garbage/empty response → `ok=False` fallback.
  - Oversized/non-image input → rejected cleanly.
- Parsing/validation logic is factored into a pure function
  (`_parse_extraction(text)`) so it is testable without Ollama.
- Manual: with `llava` pulled, upload a sample grade image and confirm fields
  pre-fill and remain editable.

## 7. Rollout / Prerequisite note for the demo

Add to README: to enable photo import, run `ollama pull llava` (or set
`VISION_MODEL`). Without it, HeronGuide still works via manual entry.
