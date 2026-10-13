"""Tests for password hashing and sign-up validation (no database needed)."""
from __future__ import annotations

import auth


def test_hash_is_salted_and_verifies():
    h1, h2 = auth.hash_password("abc12345"), auth.hash_password("abc12345")
    assert h1 != h2                      # random salt
    assert "abc12345" not in h1
    assert auth.verify_password("abc12345", h1)
    assert not auth.verify_password("abc12346", h1)


def test_verify_rejects_garbage_hash():
    assert not auth.verify_password("x", "not-a-hash")
    assert not auth.verify_password("x", "bcrypt$1$2$3$4$5")


def test_normalize_email():
    assert auth.normalize_email("  Juan@Example.COM ") == "juan@example.com"


def test_validate_signup():
    ok = ("Juan Dela Cruz", "juan@example.com", "abc12345", "abc12345")
    assert auth.validate_signup(*ok) is None
    assert auth.validate_signup("J", *ok[1:]) is not None
    assert auth.validate_signup(ok[0], "bad-email", ok[2], ok[3]) is not None
    assert auth.validate_signup(ok[0], ok[1], "short1", "short1") is not None
    assert auth.validate_signup(ok[0], ok[1], "onlyletters", "onlyletters") is not None
    assert auth.validate_signup(ok[0], ok[1], "abc12345", "abc99999") is not None
