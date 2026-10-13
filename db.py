"""PostgreSQL connection helper for HeronGuide.

Connection string comes from the ``DATABASE_URL`` environment variable, or
from ``DATABASE_URL`` in ``.streamlit/secrets.toml``:

    DATABASE_URL = "postgresql://heron:YOUR_PASSWORD@localhost:5432/heronguide"
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

_SCHEMA_FILE = Path(__file__).with_name("schema.sql")


class DatabaseConfigError(RuntimeError):
    """DATABASE_URL is missing."""


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st

        return str(st.secrets["DATABASE_URL"])
    except Exception as exc:  # noqa: BLE001 - no secrets file / no key
        raise DatabaseConfigError(
            "DATABASE_URL is not set. Add it to .streamlit/secrets.toml or "
            "set it as an environment variable."
        ) from exc


def connect() -> psycopg.Connection:
    """Open a new connection. Use as ``with connect() as conn:`` (commits on
    success, rolls back on error, closes at the end)."""
    return psycopg.connect(_database_url(), row_factory=dict_row, connect_timeout=5)


def ensure_schema() -> None:
    """Create the tables if they don't exist yet (idempotent)."""
    with connect() as conn:
        conn.execute(_SCHEMA_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    ensure_schema()
    print("Schema is ready.")
