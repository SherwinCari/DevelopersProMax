"""Tests for grade photo extraction parsing (grade-photo-import Tasks 1-2).

These exercise the pure parsing/validation path only; no live vision model.
"""
from __future__ import annotations

from vision import GradeExtraction, _parse_extraction, extract_grades


def test_well_formed_json():
    r = _parse_extraction('{"gwa": 88, "math": 90, "english": 85, "shs_track": "STEM"}')
    assert r.ok is True
    assert r.gwa == 88 and r.math == 90 and r.english == 85
    assert r.shs_track == "STEM"
    assert set(r.filled_fields) == {"GWA", "Math", "English", "SHS strand"}


def test_json_embedded_in_prose():
    text = (
        "Sure! Here are the grades I found:\n"
        '{"gwa": 91.5, "math": 87, "english": 84, "shs_track": "ICT"}\n'
        "Let me know if you need anything else."
    )
    r = _parse_extraction(text)
    assert r.ok is True
    assert r.gwa == 91.5 and r.math == 87 and r.english == 84
    assert r.shs_track == "ICT (TVL)"  # mapped to catalog track


def test_out_of_range_values_dropped_with_note():
    r = _parse_extraction('{"gwa": 150, "math": 90, "english": 60, "shs_track": null}')
    assert r.gwa is None          # 150 out of range -> dropped
    assert r.english is None       # 60 below 75 -> dropped
    assert r.math == 90
    assert r.ok is True            # at least one field read
    assert "out-of-range" in r.notes.lower()


def test_nulls_are_handled():
    r = _parse_extraction('{"gwa": null, "math": null, "english": null, "shs_track": null}')
    assert r.ok is False
    assert r.gwa is None and r.math is None and r.english is None
    assert "manually" in r.notes.lower()


def test_garbage_response_is_fallback():
    r = _parse_extraction("I'm not sure, the image is blurry.")
    assert r.ok is False
    assert "manually" in r.notes.lower()


def test_empty_response_is_fallback():
    r = _parse_extraction("")
    assert r.ok is False


def test_unknown_track_becomes_none():
    r = _parse_extraction('{"gwa": 90, "math": 90, "english": 90, "shs_track": "Underwater Basket Weaving"}')
    assert r.shs_track is None
    assert r.ok is True  # grades still read


def test_extract_grades_rejects_empty_bytes():
    r = extract_grades(b"")
    assert r.ok is False
    assert isinstance(r, GradeExtraction)


def test_extract_grades_rejects_oversized_image():
    big = b"x" * (10 * 1024 * 1024 + 1)
    r = extract_grades(big)
    assert r.ok is False
    assert "10 mb" in r.notes.lower()
