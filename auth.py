"""Account logic for HeronGuide: validation, password hashing, sign-up, login.

Passwords are hashed with scrypt (Python standard library) using a random
per-user salt. Only the hash is stored. All SQL uses bound parameters.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from typing import Optional

from psycopg import errors as pg_errors

import db

MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15
MIN_PASSWORD_LEN = 8

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Returned for any login failure so the form never reveals which emails exist.
BAD_LOGIN = "Incorrect email or password."


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested, no database)
# ---------------------------------------------------------------------------
def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_signup(full_name: str, email: str, password: str, confirm: str) -> Optional[str]:
    """Return an error message, or None if the input is acceptable."""
    name = (full_name or "").strip()
    if not 2 <= len(name) <= 100:
        return "Enter your full name (2–100 characters)."
    if len(normalize_email(email)) > 254 or not _EMAIL_RE.match(normalize_email(email)):
        return "Enter a valid email address."
    if len(password or "") < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        return "Password must include at least one letter and one number."
    if len(password) > 128:
        return "Password is too long (max 128 characters)."
    if password != confirm:
        return "Passwords do not match."
    return None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32
    )
    b64 = lambda b: base64.b64encode(b).decode("ascii")  # noqa: E731
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${b64(salt)}${b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        digest = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
        )
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


# Used to spend the same time on unknown emails as on real ones.
_DUMMY_HASH = hash_password("not-a-real-password-1")


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------
def register(full_name: str, email: str, password: str, confirm: str):
    """Create an account. Returns ``(user_dict, None)`` or ``(None, error)``."""
    error = validate_signup(full_name, email, password, confirm)
    if error:
        return None, error
    try:
        with db.connect() as conn:
            row = conn.execute(
                "INSERT INTO users (full_name, email, password_hash) "
                "VALUES (%s, %s, %s) RETURNING id, full_name, email",
                (full_name.strip(), normalize_email(email), hash_password(password)),
            ).fetchone()
    except pg_errors.UniqueViolation:
        return None, "An account with this email already exists. Try signing in."
    return row, None


def login(email: str, password: str):
    """Check credentials. Returns ``(user_dict, None)`` or ``(None, error)``."""
    email = normalize_email(email)
    if not email or not password:
        return None, "Enter your email and password."

    with db.connect() as conn:
        row = conn.execute(
            "SELECT id, full_name, email, password_hash, "
            "       (locked_until IS NOT NULL AND locked_until > now()) AS is_locked, "
            "       CEIL(EXTRACT(EPOCH FROM (locked_until - now())) / 60) AS minutes_left "
            "FROM users WHERE email = %s",
            (email,),
        ).fetchone()

        if row is None:
            verify_password(password, _DUMMY_HASH)  # timing equalizer
            return None, BAD_LOGIN

        if row["is_locked"]:
            return None, f"Too many failed attempts. Try again in {int(row['minutes_left'])} minute(s)."

        if not verify_password(password, row["password_hash"]):
            conn.execute(
                "UPDATE users SET failed_attempts = failed_attempts + 1, "
                "  locked_until = CASE WHEN failed_attempts + 1 >= %s "
                "                      THEN now() + make_interval(mins => %s) END "
                "WHERE id = %s",
                (MAX_FAILED_ATTEMPTS, LOCK_MINUTES, row["id"]),
            )
            return None, BAD_LOGIN

        conn.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL, "
            "last_login_at = now() WHERE id = %s",
            (row["id"],),
        )
        return {"id": row["id"], "full_name": row["full_name"], "email": row["email"]}, None


__all__ = [
    "register", "login", "validate_signup", "hash_password", "verify_password",
    "normalize_email", "BAD_LOGIN",
]
