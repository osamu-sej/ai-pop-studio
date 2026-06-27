"""Source ingestion pipeline.

extract → store source → chunk → embed → store chunks → summarise.

Embedding + summarisation happen at write time so chat/search stay fast.
"""

from __future__ import annotations

from pathlib import Path

from .. import repositories as repo
from ..ai import engine
from ..config import get_settings
from . import chunking, extractors, vectorstore


def _index_source(source: dict) -> dict:
    """Chunk + embed + summarise a freshly stored source."""
    settings = get_settings()
    text = source["content"]
    chunks = chunking.chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    embeddings = None
    if chunks:
        try:
            embeddings = vectorstore.embed_chunks(chunks)
        except Exception:
            embeddings = None
    repo.replace_chunks(source["id"], source["notebook_id"], chunks, embeddings)

    summary = ""
    if text.strip():
        try:
            summary = engine.summarize_source(text)
        except Exception:
            summary = ""
    if summary:
        repo.update_source_summary(source["id"], summary)
    repo.set_source_status(source["id"], "ready")
    return repo.get_source(source["id"])


def ingest_text(notebook_id: str, title: str, content: str) -> dict:
    title, text, stype, meta = extractors.extract_text(title, content)
    source = repo.create_source(notebook_id, title, stype, text, origin="", metadata=meta)
    return _index_source(source)


def ingest_url(notebook_id: str, url: str, title: str | None = None) -> dict:
    title_out, text, stype, meta = extractors.extract_url(url, title)
    source = repo.create_source(notebook_id, title_out, stype, text, origin=url, metadata=meta)
    return _index_source(source)


def ingest_file(notebook_id: str, filename: str, data: bytes) -> dict:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        title, text, stype, meta = extractors.extract_pdf(data, filename)
    elif ext == ".docx":
        title, text, stype, meta = extractors.extract_docx(data, filename)
    elif ext in {".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg", ".flac"}:
        return _ingest_audio(notebook_id, filename, data)
    else:  # .txt, .md, .csv, .json, code, anything text-like
        title, text, stype, meta = extractors.extract_text_bytes(data, filename)
    source = repo.create_source(notebook_id, title, stype, text, origin=filename, metadata=meta)
    return _index_source(source)


def _ingest_audio(notebook_id: str, filename: str, data: bytes) -> dict:
    settings = get_settings()
    if not extractors.whisper_available():
        # Store a placeholder so the user knows what's needed — no crash.
        source = repo.create_source(
            notebook_id, filename, "audio",
            content="",
            origin=filename,
            summary="Audio transcription needs the optional 'faster-whisper' package "
                    "(pip install -r requirements-extras.txt). The file was saved but not transcribed.",
            status="needs_stt",
            metadata={"filename": filename},
        )
        return source
    tmp = settings.uploads_dir / filename
    tmp.write_bytes(data)
    title, text, stype, meta = extractors.extract_audio(tmp, filename, settings.stt_model)
    source = repo.create_source(notebook_id, title, stype, text, origin=filename, metadata=meta)
    return _index_source(source)


def reindex_source(source_id: str) -> dict | None:
    source = repo.get_source(source_id)
    if not source:
        return None
    return _index_source(source)
