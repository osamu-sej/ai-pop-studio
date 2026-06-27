"""SQLite storage layer.

A single embedded SQLite database keeps Aurora dependency-free and portable —
no external database server, no cloud, no API. Vector embeddings are stored
inline (as packed float32 blobs) and similarity is computed in-process with
numpy. This is plenty fast for personal/research-scale notebooks and keeps the
whole stack on-device.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from .config import get_settings

_local = threading.local()


SCHEMA = """
CREATE TABLE IF NOT EXISTS notebooks (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    emoji       TEXT NOT NULL DEFAULT '📓',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id           TEXT PRIMARY KEY,
    notebook_id  TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    source_type  TEXT NOT NULL,           -- pdf | web | youtube | text | docx | audio
    origin       TEXT NOT NULL DEFAULT '',-- url / filename
    content      TEXT NOT NULL DEFAULT '',
    summary      TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'ready',
    metadata     TEXT NOT NULL DEFAULT '{}',
    token_count  INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sources_notebook ON sources(notebook_id);

CREATE TABLE IF NOT EXISTS chunks (
    id           TEXT PRIMARY KEY,
    source_id    TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    notebook_id  TEXT NOT NULL,
    idx          INTEGER NOT NULL,
    text         TEXT NOT NULL,
    embedding    BLOB,                    -- packed float32 vector
    dim          INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_chunks_notebook ON chunks(notebook_id);

CREATE TABLE IF NOT EXISTS notes (
    id           TEXT PRIMARY KEY,
    notebook_id  TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    content      TEXT NOT NULL DEFAULT '',
    note_type    TEXT NOT NULL DEFAULT 'note',  -- note | generated
    kind         TEXT NOT NULL DEFAULT '',       -- summary/study_guide/faq/...
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notes_notebook ON notes(notebook_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    id           TEXT PRIMARY KEY,
    notebook_id  TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    role         TEXT NOT NULL,           -- user | assistant
    content      TEXT NOT NULL,
    citations    TEXT NOT NULL DEFAULT '[]',
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_notebook ON chat_messages(notebook_id);

CREATE TABLE IF NOT EXISTS podcasts (
    id           TEXT PRIMARY KEY,
    notebook_id  TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    transcript   TEXT NOT NULL DEFAULT '',
    audio_path   TEXT NOT NULL DEFAULT '',
    status       TEXT NOT NULL DEFAULT 'ready',
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_podcasts_notebook ON podcasts(notebook_id);
"""


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    settings.ensure_dirs()
    conn = sqlite3.connect(str(settings.database_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def get_connection() -> sqlite3.Connection:
    """One connection per thread (FastAPI runs handlers in a threadpool)."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _connect()
        _local.conn = conn
    return conn


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
