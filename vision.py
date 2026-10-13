"""Grade photo import for HeronGuide (vision model via Ollama).

Reads grades from an uploaded image and returns an editable *draft*. It never
decides eligibility — the deterministic rule engine in ``rules.py`` still does
that, and the extracted values are shown in editable fields the student must
confirm. Every call has a timeout and degrades to manual entry on any failure,
mirroring the resilience pattern in ``advisor.py``.

The configured model is TEXT-SEPARATE from the advisor's model: ``VISION_MODEL``
(default ``llava``) must be a vision-capable model. ``llama3.1:8b`` cannot read
images, so this module checks for a vision model specifically.
"""
from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from typing import Callable, Optional

from data.programs import GRADE_MAX, GRADE_MIN, SHS_TRACKS

VISION_MODEL = os.environ.get("VISION_MODEL", "llava")
# Text model used to read grades out of extracted DOCX/PDF text (no vision needed).
TEXT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
_DEFAULT_TIMEOUT = 90.0
_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
_MAX_DOC_BYTES = 20 * 1024 * 1024  # 20 MB for PDF/DOCX
# Below this many characters of extracted text, treat a PDF as scanned (image).
_MIN_TEXT_CHARS = 25

# Supported upload extensions (used by the UI uploader and dispatcher).
IMAGE_EXTS = ("png", "jpg", "jpeg", "webp")
DOC_EXTS = ("pdf", "docx")
SUPPORTED_EXTS = IMAGE_EXTS + DOC_EXTS

_TEXT_SYSTEM = (
    "You read a student's grades from the text of a report card or grade slip. "
    "Return ONLY a single JSON object and nothing else. Never guess: use null for "
    "any value not clearly present. Grades are on a 0-100 scale."
)

_TEXT_INSTRUCTION = (
    "From the document text below, extract these fields and return JSON exactly "
    "in this shape:\n"
    '{"gwa": number|null, "math": number|null, "english": number|null, '
    '"shs_track": string|null}\n'
    "gwa = general weighted average / overall average. "
    "math = the mathematics subject grade. english = the english subject grade. "
    "shs_track = the SHS strand if present (e.g. STEM, ICT, ABM, HUMSS), else null. "
    "Return only the JSON object.\n\n--- DOCUMENT TEXT ---\n"
)

_SYSTEM = (
    "You read a student's grades from an image of a report card or grade slip. "
    "Return ONLY a single JSON object and nothing else. Never guess: use null for "
    "any value that is not clearly visible. Grades are on a 0-100 scale."
)

_USER_INSTRUCTION = (
    "Extract these fields and return JSON exactly in this shape:\n"
    '{"gwa": number|null, "math": number|null, "english": number|null, '
    '"shs_track": string|null}\n'
    "gwa = general weighted average / overall average. "
    "math = the mathematics subject grade. "
    "english = the english subject grade. "
    "shs_track = the senior high school strand if shown (e.g. STEM, ICT, ABM, "
    "HUMSS), else null. Return only the JSON object."
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
@dataclass
class GradeExtraction:
    """Draft values read from an image. All fields may be None if unreadable."""

    gwa: Optional[float] = None
    math: Optional[float] = None
    english: Optional[float] = None
    shs_track: Optional[str] = None
    raw_text: str = ""
    notes: str = ""
    ok: bool = False

    @property
    def filled_fields(self) -> list[str]:
        out = []
        if self.gwa is not None:
            out.append("GWA")
        if self.math is not None:
            out.append("Math")
        if self.english is not None:
            out.append("English")
        if self.shs_track:
            out.append("SHS strand")
        return out


# ---------------------------------------------------------------------------
# Ollama client (shares the host-resolution logic used by the advisor)
# ---------------------------------------------------------------------------
def _resolve_host() -> str:
    raw = (os.environ.get("OLLAMA_HOST") or "").strip()
    if not raw:
        return "http://127.0.0.1:11434"
    host = raw if "://" in raw else f"http://{raw}"
    return host.replace("0.0.0.0", "127.0.0.1").replace("localhost", "127.0.0.1")


OLLAMA_HOST = _resolve_host()


def _client():
    import ollama

    return ollama.Client(host=OLLAMA_HOST)


def _run_with_timeout(fn: Callable[[], str], timeout: float) -> str:
    box: dict[str, object] = {}

    def worker() -> None:
        try:
            box["value"] = fn()
        except Exception as exc:  # noqa: BLE001
            box["error"] = exc

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError(f"Vision call exceeded {timeout}s")
    if "error" in box:
        raise box["error"]  # type: ignore[misc]
    return str(box.get("value", "")).strip()


def vision_available() -> bool:
    """True only if the Ollama server answers and VISION_MODEL is pulled."""

    def probe() -> str:
        names = [m.model for m in _client().list().models]
        want = VISION_MODEL.split(":")[0]
        return "yes" if any(n and n.split(":")[0] == want for n in names) else ""

    try:
        return bool(_run_with_timeout(probe, 3.0))
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Pure parsing / validation (unit-tested without a live model)
# ---------------------------------------------------------------------------
def _coerce_grade(value: object) -> Optional[float]:
    """Return a float in [GRADE_MIN, GRADE_MAX], else None."""
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if GRADE_MIN <= num <= GRADE_MAX:
        return round(num, 2)
    return None


def _match_track(value: object) -> Optional[str]:
    """Map a free-text strand to one of the known SHS_TRACKS, else None."""
    if not value or not isinstance(value, str):
        return None
    v = value.strip().lower()
    if not v:
        return None
    for track in SHS_TRACKS:
        key = track.lower()
        if v == key or v in key or key.split(" ")[0] in v:
            return track
    return None


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first JSON object out of a model response, tolerating extra prose."""
    if not text:
        return None
    # Prefer a fenced or inline {...} block; take the first balanced-looking one.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    candidate = match.group(0) if match else text
    try:
        data = json.loads(candidate)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _parse_extraction(text: str) -> GradeExtraction:
    """Turn raw model text into a validated GradeExtraction (pure function)."""
    data = _extract_json(text)
    if data is None:
        return GradeExtraction(
            raw_text=text,
            ok=False,
            notes="Couldn't read grades from the image. Please enter them manually.",
        )

    gwa = _coerce_grade(data.get("gwa"))
    math = _coerce_grade(data.get("math"))
    english = _coerce_grade(data.get("english"))
    track = _match_track(data.get("shs_track"))

    dropped = []
    for key in ("gwa", "math", "english"):
        if data.get(key) is not None and _coerce_grade(data.get(key)) is None:
            dropped.append(key.upper())

    result = GradeExtraction(
        gwa=gwa, math=math, english=english, shs_track=track, raw_text=text,
    )
    found = result.filled_fields
    if found:
        result.ok = True
        note = "Read from your file: " + ", ".join(found) + ". Please double-check."
        if dropped:
            note += (
                " Ignored out-of-range value(s) for "
                + ", ".join(dropped)
                + " (grades must be 75-100)."
            )
        result.notes = note
    else:
        result.ok = False
        result.notes = (
            "Couldn't confidently read any grade from the image. "
            "Please enter them manually."
        )
    return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def extract_grades(image_bytes: bytes, timeout: float = _DEFAULT_TIMEOUT) -> GradeExtraction:
    """Read grades from an image. Always returns a GradeExtraction, never raises.

    On any problem (missing model, oversized/invalid image, timeout, parse
    failure) returns ``ok=False`` with a note so the UI falls back to manual.
    """
    if not image_bytes:
        return GradeExtraction(ok=False, notes="No image was provided.")
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        return GradeExtraction(
            ok=False,
            notes="That image is larger than 10 MB. Please use a smaller photo.",
        )

    def call() -> str:
        resp = _client().chat(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": _USER_INSTRUCTION,
                    "images": [image_bytes],
                },
            ],
            options={"temperature": 0.1},
        )
        return resp["message"]["content"]

    try:
        text = _run_with_timeout(call, timeout)
    except Exception:  # noqa: BLE001 - demo must never crash
        return GradeExtraction(
            ok=False,
            notes="The photo reader isn't responding. Please enter your grades manually.",
        )
    return _parse_extraction(text)


# ---------------------------------------------------------------------------
# Document text extraction (DOCX / text-based PDF) — no model needed
# ---------------------------------------------------------------------------
def _docx_to_text(data: bytes) -> str:
    """Extract text from a .docx file (paragraphs + table cells)."""
    import io

    import docx  # python-docx

    doc = docx.Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts).strip()


def _pdf_to_text(data: bytes) -> str:
    """Extract embedded text from a PDF (empty/short for scanned PDFs)."""
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 - skip unreadable pages
            continue
    return "\n".join(pages).strip()


def _pdf_first_page_image(data: bytes) -> Optional[bytes]:
    """Render the first PDF page to PNG bytes (for scanned PDFs via the vision model)."""
    try:
        import fitz  # PyMuPDF

        pdf = fitz.open(stream=data, filetype="pdf")
        if pdf.page_count == 0:
            return None
        page = pdf.load_page(0)
        pix = page.get_pixmap(dpi=150)
        return pix.tobytes("png")
    except Exception:  # noqa: BLE001
        return None


def _extract_from_text(text: str, timeout: float) -> GradeExtraction:
    """Read grades out of plain document text using the TEXT model."""
    if not text or len(text) < _MIN_TEXT_CHARS:
        return GradeExtraction(ok=False, notes="No readable text found in the document.")

    def call() -> str:
        resp = _client().chat(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": _TEXT_SYSTEM},
                {"role": "user", "content": _TEXT_INSTRUCTION + text[:6000]},
            ],
            options={"temperature": 0.1},
        )
        return resp["message"]["content"]

    try:
        raw = _run_with_timeout(call, timeout)
    except Exception:  # noqa: BLE001
        return GradeExtraction(
            ok=False,
            notes="The document reader isn't responding. Please enter your grades manually.",
        )
    return _parse_extraction(raw)


def _ext_of(filename: str) -> str:
    return (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()


# ---------------------------------------------------------------------------
# Unified upload entry point (image, pdf, or docx)
# ---------------------------------------------------------------------------
def extract_grades_from_upload(
    data: bytes, filename: str, timeout: float = _DEFAULT_TIMEOUT
) -> GradeExtraction:
    """Read grades from an uploaded image, PDF, or DOCX. Never raises.

    * images  -> vision model (needs VISION_MODEL)
    * .docx   -> extract text, read with the TEXT model
    * .pdf    -> try embedded text first; if scanned, render page 1 and use vision
    """
    if not data:
        return GradeExtraction(ok=False, notes="No file was provided.")

    ext = _ext_of(filename)

    if ext in IMAGE_EXTS:
        return extract_grades(data, timeout)

    if ext not in DOC_EXTS:
        return GradeExtraction(
            ok=False,
            notes="Unsupported file type. Upload a PNG/JPG image, a PDF, or a DOCX.",
        )

    if len(data) > _MAX_DOC_BYTES:
        return GradeExtraction(
            ok=False, notes="That document is larger than 20 MB. Please use a smaller file."
        )

    if ext == "docx":
        try:
            text = _docx_to_text(data)
        except Exception:  # noqa: BLE001
            return GradeExtraction(
                ok=False, notes="Couldn't open that DOCX file. Please enter grades manually."
            )
        return _extract_from_text(text, timeout)

    # ext == "pdf": prefer embedded text; fall back to vision on scanned PDFs.
    try:
        text = _pdf_to_text(data)
    except Exception:  # noqa: BLE001
        text = ""

    if len(text) >= _MIN_TEXT_CHARS:
        return _extract_from_text(text, timeout)

    # Likely a scanned PDF — render the first page and use the vision model.
    img = _pdf_first_page_image(data)
    if img is None:
        return GradeExtraction(
            ok=False,
            notes="This PDF has no readable text and couldn't be converted to an image. "
            "Please upload a photo or enter grades manually.",
        )
    result = extract_grades(img, timeout)
    if not result.ok and "vision model" in result.notes.lower():
        # vision model missing: give a clearer message for scanned PDFs
        result.notes = (
            "This looks like a scanned PDF, which needs a local vision model "
            "(e.g. `llava`) to read. Please upload a photo or enter grades manually."
        )
    return result
