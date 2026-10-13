# Requirements — Grade Photo Import (HeronGuide feature)

## Overview

A new capability on the HeronGuide **Home** tab, placed beside the existing
"Check your eligibility" form: a panel prompting *"Insert grade photo for faster
result."* A student can upload a photo of their grades (e.g. a report card or SHS
grade slip). A **vision-capable local AI model** reads the image, extracts the
relevant grades (GWA, Math, English, and — if present — SHS track), and
**pre-fills the eligibility form**. The student reviews/corrects the values, then
runs the normal evaluation.

This feature extends the main spec at `.kiro/specs/heronguide/`. It does **not**
change how verdicts are decided: the deterministic rule engine in `rules.py`
remains the only thing that computes eligibility. The vision model only performs
data entry (reading numbers from an image), and its output is always editable
before evaluation.

## Critical Constraint (read first)

The currently installed model, `llama3.1:8b`, is **text-only and cannot read
images**. This feature therefore requires a **vision-capable Ollama model**
(e.g. `llava`, `llama3.2-vision`, `minicpm-v`, or `moondream`) to be pulled
locally. Because this is a prototype and model availability is the school's
choice, the feature MUST degrade gracefully to manual entry whenever a vision
model is unavailable, slow, or returns low-confidence output.

## Goals

- Let a student fill the eligibility form faster by uploading a grade photo.
- Keep the student in control: extracted values are a **draft**, always editable.
- Preserve HeronGuide's trust model — the rule engine still decides every verdict.
- Stay demo-safe: never block or crash if the vision model is missing/slow.
- Keep everything local and private (no image leaves the machine).

## Non-Goals

- Not an authoritative transcript reader; extraction is best-effort assistance.
- Does not auto-submit; a human must confirm the values before evaluation.
- Does not store, transmit, or retain uploaded images beyond the session.
- Not responsible for every document layout; unreadable images fall back to manual.

## Definitions

- **Vision model** — an Ollama model that accepts image input (e.g. `llava`).
- **Extraction** — the model's structured reading of grades from the image.
- **Confidence** — a simple signal (per field or overall) of how sure the
  extraction is; low confidence prompts the student to double-check.

## User Stories & Acceptance Criteria

### Story A — Upload a grade photo to pre-fill the form
**As a** prospective student with a photo of my grades
**I want to** upload the image and have my grades read automatically
**so that** I don't have to type each value.

Acceptance Criteria:
1. The Home eligibility area SHALL show a clearly labeled panel: *"Insert grade
   photo for faster result."*
2. The uploader SHALL accept common image types (PNG, JPG/JPEG, WEBP) and a
   reasonable size limit (e.g. ≤ 10 MB).
3. WHEN an image is uploaded AND a vision model is available, THEN the system
   SHALL attempt to extract GWA, Math, English, and SHS track.
4. WHEN extraction succeeds, THEN the extracted values SHALL populate the
   corresponding form fields as an editable draft (never auto-submitted).
5. The system SHALL show which fields were auto-filled and prompt the student to
   verify them before evaluating.

### Story B — Review and correct before evaluating
**As a** student whose photo was read by the AI
**I want to** see and edit the extracted values
**so that** an OCR mistake never produces a wrong verdict.

Acceptance Criteria:
1. Extracted values SHALL be shown in the same editable inputs used for manual entry.
2. WHEN a field could not be read, THEN it SHALL be left blank/unchanged and
   flagged so the student fills it in.
3. The eligibility evaluation SHALL run only when the student explicitly presses
   the existing "Evaluate eligibility" button.
4. The same 75–100 validation SHALL apply to extracted values.

### Story C — Graceful fallback when vision is unavailable
**As a** user on a machine without a vision model (or with a slow one)
**I want** the app to tell me clearly and let me type my grades
**so that** the tool still works and the demo never breaks.

Acceptance Criteria:
1. WHEN no vision model is available, THEN the panel SHALL show a short notice
   (e.g. "Photo reading needs a vision model — enter grades manually for now")
   and SHALL NOT error.
2. WHEN the vision call times out or fails, THEN the system SHALL inform the
   student and keep the manual form fully usable.
3. The feature SHALL never prevent the existing manual flow from working.

## Non-Functional Requirements

1. **Trust preserved:** The rule engine remains the sole decider of eligibility;
   the vision model only reads numbers into editable fields.
2. **Privacy:** Uploaded images SHALL be processed locally and not persisted
   beyond the current session; no network upload to third parties.
3. **Demo resilience:** Vision calls SHALL have a timeout and a manual-entry
   fallback, mirroring the existing advisor resilience pattern.
4. **Model-agnostic:** The configured vision model name SHALL be centralized/
   overridable (e.g. an env var) so the school can swap models.
5. **Branding/UX:** The panel SHALL match the UMak theme and sit beside the
   eligibility form without crowding it.
6. **Safety:** The feature SHALL validate that uploads are images and handle
   corrupt/unsupported files without crashing.

## Dependencies / Prerequisites

- A vision-capable Ollama model pulled locally (default suggestion: `llava`).
- The existing `ollama` Python client and the host-resolution fix already in
  `advisor.py` (`OLLAMA_HOST` normalized to `127.0.0.1`).
