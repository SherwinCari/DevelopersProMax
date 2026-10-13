# Tasks — HeronGuide (UMak CCIS Smart Admission Advisor)

Incremental, demoable, test-driven. Each task ends in a runnable/verifiable state.
Status legend: `[ ]` todo · `[~]` in progress · `[x]` done.

- [x] 1. Project skeleton + UMak theme foundation
  - Create `app.py`, `ui_theme.py`, `.streamlit/config.toml`, `requirements.txt`, `tests/`.
  - UMak navy/gold theme + custom CSS header, badges, result-card styles.
  - Pin `requirements.txt` to installed versions; ensure `pytest` present.
  - _Verify:_ `streamlit run app.py` launches a themed landing page, no errors.
  - _Requirements: NFR Branding, NFR Privacy._

- [x] 2. Program data model (CCIS, extensible)
  - `data/programs.py`: `UMCETTier`, `ProgramType`, `Program` dataclass, catalog.
  - Seed CCIS degrees (GWA ≥ 85, Math ≥ 85, English ≥ 83, UMCET ≥ Low Average)
    and diplomas (GWA ≥ 80). Helpers: `programs_for`, `all_programs`, `get_program`.
  - _Verify:_ `tests/test_programs.py` green (fields, tier order, cutoffs).
  - _Requirements: Confirmed Rules, NFR Extensibility._

- [ ] 3. Deterministic rule engine (TDD)
  - Write `tests/test_rules.py` first: fully qualified; fail-by-1% exact gap;
    Below-Average UMCET → diploma fallback; UMCET-not-received → PENDING; SHS
    track non-gating.
  - Implement `rules.py`: `StudentInput`, `Status`, `Gap`, `ProgramResult`,
    `evaluate()`, `alternatives()`. All numeric decisions here, none in the LLM.
  - _Verify:_ full pytest suite green.
  - _Requirements: Story 1 (2,3,4), Story 2 (1,2,3), Story 3 (1,2), NFR Determinism._

- [ ] 4. LLM advisor — explanation + review recommendations, with fallback
  - `advisor.py`: `explain(student, results)`, `recommend_review(student, program)`.
  - Constrained prompts (never change the verdict); timeout + templated fallback.
  - `tests/test_advisor.py` with Ollama mocked; manual live check with llama3.1:8b.
  - _Verify:_ disqualified → warm diploma routing; qualified → review checklist;
    fallback text appears when the client is forced to error.
  - _Requirements: Story 3 (1,2,3), Story 4 (1), NFR Determinism, NFR Demo resilience._

- [ ] 5. Wire UI — input flow
  - SHS track dropdown; GWA/Math/English inputs (75–100 validation); UMCET tier
    selector; "UMCET not received yet" toggle switching to pre-screening mode.
  - _Verify:_ out-of-range rejected; toggle hides tier and changes engine mode.
  - _Requirements: Story 1 (1,3,4), Story 2 (1), NFR Input validation._

- [ ] 6. Wire UI — results + advisor display
  - Per-program themed status cards (green/amber) with exact gap callouts;
    alternatives section; AI explanation panel with spinner.
  - _Verify:_ qualified vs disqualified students render correct card states
    end-to-end.
  - _Requirements: Story 1 (2), Story 2 (1,2), Story 3 (1,2), NFR Branding._

- [ ] 7. Practice interview module (Story 4)
  - `st.session_state` Q&A shown only when qualified: 3–4 LLM questions one at a
    time + brief feedback; skip/finish control; question-bank fallback.
  - _Verify:_ flow advances correctly; works with Ollama off (fallback).
  - _Requirements: Story 4 (1,2,3), NFR Demo resilience._

- [ ] 8. Hackathon polish + demo assets
  - Seeded example-student buttons: (a) clear pass → review + interview,
    (b) fail-by-1% → exact gap + empathy, (c) diploma fallback → alternative routing.
  - Privacy/offline badge, loading states, final theme pass, `README.md`, pitch tagline.
  - _Verify:_ each example button produces its intended narrative/path.
  - _Requirements: all stories (demo coverage), NFR Branding._

- [ ] 9. End-to-end rehearsal + resilience check
  - Full run with Ollama ON and OFF (fallbacks), check timings, edge inputs, cleanup.
  - _Verify:_ stable prototype; pytest green; no console errors; all three arcs work.
  - _Requirements: NFR Demo resilience, NFR Privacy._

## Verification Summary
- `tests/` (Tasks 2, 3, 4, 7) all green before final.
- `streamlit run app.py`, then walk the three seeded scenarios with Ollama on and off.
- Confirm theme renders and the console is clean.
