# Tasks — Grade Photo Import (HeronGuide feature)

Extends the main HeronGuide spec. Incremental and demo-safe; the manual flow must
keep working at every step. Status: `[ ]` todo · `[~]` in progress · `[x]` done.

- [ ] 1. Vision model prerequisite + detection
  - Document `ollama pull llava` (and `VISION_MODEL` override) in README.
  - Add `vision_available()` in a new `vision.py`, reusing the host-resolution
    and timeout patterns from `advisor.py`.
  - _Verify:_ `vision_available()` returns True only when a vision model is pulled;
    returns False (no crash) otherwise.
  - _Requirements: Critical Constraint, Story C (1), NFR Model-agnostic._

- [ ] 2. Extraction + parsing core (`vision.py`, TDD)
  - Define `GradeExtraction` dataclass and `extract_grades(image_bytes)`.
  - Factor parsing into pure `_parse_extraction(text)`; strict JSON prompt;
    coerce numbers; drop out-of-range (not 75–100) to null with a note.
  - Timeout + fallback → `GradeExtraction(ok=False, notes=...)` on any failure.
  - Write `tests/test_vision.py` first (well-formed JSON, JSON-in-prose,
    out-of-range, garbage/empty, oversized/non-image).
  - _Verify:_ pytest suite green; no live model required for tests.
  - _Requirements: Story A (3), Story B (4), Story C (2), NFR Demo resilience, NFR Privacy._

- [ ] 3. Home UI — photo panel
  - In `views/home.py`, add the "Insert grade photo for faster result" panel
    above the grade inputs inside the eligibility container.
  - `st.file_uploader` (png/jpg/jpeg/webp, ≤10 MB) + "Read grades from photo"
    button; disabled with a notice when `vision_available()` is False.
  - _Verify:_ panel renders in the UMak theme; disabled-state notice shows when
    no vision model; manual form still fully usable.
  - _Requirements: Story A (1,2), Story C (1), NFR Branding._

- [ ] 4. Wire extraction into the form (pre-fill, editable)
  - On button click: validate image, call `extract_grades`, seed
    `in_gwa/in_math/in_eng/in_track` session keys, `st.rerun()`.
  - Show which fields were auto-filled + a "please verify" prompt; blanks for
    unread fields. Evaluation still runs only via the existing button.
  - _Verify:_ uploading a grade image pre-fills editable values; a wrong read can
    be corrected before evaluating; low/failed read shows a warning and manual
    entry works.
  - _Requirements: Story A (4,5), Story B (1,2,3), Story C (2,3)._

- [ ] 5. Resilience + privacy pass
  - Confirm no image is written to disk or sent anywhere; images cleared from
    state after extraction. Verify timeout/fallback with the vision model off.
  - _Verify:_ with vision model stopped, panel degrades to manual with a clear
    message; app never errors.
  - _Requirements: Story C (1,2,3), NFR Privacy, NFR Demo resilience, NFR Safety._

- [ ] 6. Docs + demo asset
  - Update README with the prerequisite and a one-line pitch for the feature.
  - Optional: include a sample grade image for the demo (clearly fake data).
  - _Verify:_ a fresh reader can enable and demo the feature from the README.
  - _Requirements: Dependencies/Prerequisites, NFR Branding._

## Verification Summary
- `tests/test_vision.py` green (parsing/validation without a live model).
- With `llava` pulled: upload a grade photo on Home → fields pre-fill, remain
  editable, and the existing rule-engine evaluation produces the verdict.
- With no vision model: panel shows the manual-entry notice; nothing breaks.
