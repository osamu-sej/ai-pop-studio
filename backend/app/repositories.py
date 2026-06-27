"""Data-access layer over SQLite.

Plain functions, grouped by entity. Embeddings are packed to float32 bytes so
they round-trip without precision drift and stay compact on disk.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from .database import get_connection, transaction
from .utils import estimate_tokens, new_id, now_iso


# ── Notebooks ──────────────────────────────────────────────────────────────
def create_notebook(name: str, description: str = "", emoji: str = "📓") -> dict:
    nid = new_id()
    ts = now_iso()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO notebooks (id, name, description, emoji, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (nid, name, description, emoji, ts, ts),
        )
    return get_notebook(nid)


def list_notebooks() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT n.*,
            (SELECT COUNT(*) FROM sources s WHERE s.notebook_id = n.id) AS source_count,
            (SELECT COUNT(*) FROM notes nt WHERE nt.notebook_id = n.id) AS note_count
        FROM notebooks n
        ORDER BY n.updated_at DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_notebook(nid: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT n.*,
            (SELECT COUNT(*) FROM sources s WHERE s.notebook_id = n.id) AS source_count,
            (SELECT COUNT(*) FROM notes nt WHERE nt.notebook_id = n.id) AS note_count
        FROM notebooks n WHERE n.id = ?
        """,
        (nid,),
    ).fetchone()
    return dict(row) if row else None


def update_notebook(nid: str, **fields: Any) -> dict | None:
    fields = {k: v for k, v in fields.items() if v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        with transaction() as conn:
            conn.execute(
                f"UPDATE notebooks SET {sets}, updated_at = ? WHERE id = ?",
                (*fields.values(), now_iso(), nid),
            )
    return get_notebook(nid)


def touch_notebook(nid: str) -> None:
    with transaction() as conn:
        conn.execute("UPDATE notebooks SET updated_at = ? WHERE id = ?", (now_iso(), nid))


def delete_notebook(nid: str) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM notebooks WHERE id = ?", (nid,))


# ── Sources ────────────────────────────────────────────────────────────────
def create_source(
    notebook_id: str,
    title: str,
    source_type: str,
    content: str,
    origin: str = "",
    summary: str = "",
    metadata: dict | None = None,
    status: str = "ready",
) -> dict:
    sid = new_id()
    with transaction() as conn:
        conn.execute(
            """INSERT INTO sources
               (id, notebook_id, title, source_type, origin, content, summary,
                status, metadata, token_count, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid, notebook_id, title, source_type, origin, content, summary,
                status, json.dumps(metadata or {}), estimate_tokens(content), now_iso(),
            ),
        )
    touch_notebook(notebook_id)
    return get_source(sid)


def list_sources(notebook_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sources WHERE notebook_id = ? ORDER BY created_at ASC",
        (notebook_id,),
    ).fetchall()
    return [_source_row(r) for r in rows]


def get_source(sid: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (sid,)).fetchone()
    return _source_row(row) if row else None


def update_source_summary(sid: str, summary: str) -> None:
    with transaction() as conn:
        conn.execute("UPDATE sources SET summary = ? WHERE id = ?", (summary, sid))


def set_source_status(sid: str, status: str) -> None:
    with transaction() as conn:
        conn.execute("UPDATE sources SET status = ? WHERE id = ?", (status, sid))


def delete_source(sid: str) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM sources WHERE id = ?", (sid,))


def _source_row(row) -> dict:
    d = dict(row)
    d["metadata"] = json.loads(d.get("metadata") or "{}")
    return d


# ── Chunks / embeddings ────────────────────────────────────────────────────
def replace_chunks(source_id: str, notebook_id: str, chunks: list[str],
                   embeddings: list[np.ndarray] | None = None) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
        for idx, text in enumerate(chunks):
            emb = embeddings[idx] if embeddings is not None else None
            blob = emb.astype(np.float32).tobytes() if emb is not None else None
            dim = int(emb.shape[0]) if emb is not None else 0
            conn.execute(
                "INSERT INTO chunks (id, source_id, notebook_id, idx, text, embedding, dim)"
                " VALUES (?,?,?,?,?,?,?)",
                (new_id(), source_id, notebook_id, idx, text, blob, dim),
            )


def get_chunks_for_notebook(notebook_id: str, source_ids: list[str] | None = None) -> list[dict]:
    conn = get_connection()
    sql = (
        "SELECT c.id, c.source_id, c.idx, c.text, c.embedding, c.dim, s.title AS source_title "
        "FROM chunks c JOIN sources s ON s.id = c.source_id WHERE c.notebook_id = ?"
    )
    params: list[Any] = [notebook_id]
    if source_ids:
        placeholders = ",".join("?" for _ in source_ids)
        sql += f" AND c.source_id IN ({placeholders})"
        params.extend(source_ids)
    rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if d["embedding"] is not None and d["dim"]:
            d["vector"] = np.frombuffer(d["embedding"], dtype=np.float32)
        else:
            d["vector"] = None
        del d["embedding"]
        out.append(d)
    return out


# ── Notes ──────────────────────────────────────────────────────────────────
def create_note(notebook_id: str, title: str, content: str = "",
                note_type: str = "note", kind: str = "") -> dict:
    nid = new_id()
    ts = now_iso()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO notes (id, notebook_id, title, content, note_type, kind, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (nid, notebook_id, title, content, note_type, kind, ts, ts),
        )
    touch_notebook(notebook_id)
    return get_note(nid)


def list_notes(notebook_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notes WHERE notebook_id = ? ORDER BY updated_at DESC",
        (notebook_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_note(nid: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (nid,)).fetchone()
    return dict(row) if row else None


def update_note(nid: str, **fields: Any) -> dict | None:
    fields = {k: v for k, v in fields.items() if v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        with transaction() as conn:
            conn.execute(
                f"UPDATE notes SET {sets}, updated_at = ? WHERE id = ?",
                (*fields.values(), now_iso(), nid),
            )
    return get_note(nid)


def delete_note(nid: str) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (nid,))


# ── Chat ───────────────────────────────────────────────────────────────────
def add_chat_message(notebook_id: str, role: str, content: str,
                     citations: list[dict] | None = None) -> dict:
    mid = new_id()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO chat_messages (id, notebook_id, role, content, citations, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (mid, notebook_id, role, content, json.dumps(citations or []), now_iso()),
        )
    return get_chat_message(mid)


def get_chat_message(mid: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM chat_messages WHERE id = ?", (mid,)).fetchone()
    return _chat_row(row) if row else None


def list_chat_messages(notebook_id: str, limit: int = 200) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chat_messages WHERE notebook_id = ? ORDER BY created_at ASC LIMIT ?",
        (notebook_id, limit),
    ).fetchall()
    return [_chat_row(r) for r in rows]


def clear_chat(notebook_id: str) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM chat_messages WHERE notebook_id = ?", (notebook_id,))


def _chat_row(row) -> dict:
    d = dict(row)
    d["citations"] = json.loads(d.get("citations") or "[]")
    return d


# ── Podcasts ───────────────────────────────────────────────────────────────
def create_podcast(notebook_id: str, title: str, transcript: str = "",
                   audio_path: str = "", status: str = "ready") -> dict:
    pid = new_id()
    with transaction() as conn:
        conn.execute(
            "INSERT INTO podcasts (id, notebook_id, title, transcript, audio_path, status, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (pid, notebook_id, title, transcript, audio_path, status, now_iso()),
        )
    return get_podcast(pid)


def list_podcasts(notebook_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM podcasts WHERE notebook_id = ? ORDER BY created_at DESC",
        (notebook_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_podcast(pid: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM podcasts WHERE id = ?", (pid,)).fetchone()
    return dict(row) if row else None


def delete_podcast(pid: str) -> None:
    with transaction() as conn:
        conn.execute("DELETE FROM podcasts WHERE id = ?", (pid,))
