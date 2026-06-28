"""Split documents into overlapping, boundary-aware chunks for retrieval."""

from __future__ import annotations

import re

_PARA = re.compile(r"\n\s*\n")


def chunk_text(text: str, chunk_size: int = 1100, overlap: int = 150) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    # Build chunks paragraph-first, then hard-split anything still too large.
    paragraphs = [p.strip() for p in _PARA.split(text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_hard_split(para, chunk_size, overlap))
            continue
        if buf and len(buf) + len(para) + 2 > chunk_size:
            chunks.append(buf)
            # carry a little overlap from the tail of the previous chunk
            buf = (buf[-overlap:] + "\n\n" + para) if overlap else para
        else:
            buf = (buf + "\n\n" + para) if buf else para
    if buf:
        chunks.append(buf)
    return [c.strip() for c in chunks if c.strip()]


def _hard_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    out = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        # try to end on a sentence boundary near the window edge
        window = text[start:end]
        m = list(re.finditer(r"[.!?。！？]\s", window))
        if end < len(text) and m and m[-1].end() > chunk_size * 0.6:
            end = start + m[-1].end()
            window = text[start:end]
        out.append(window.strip())
        start += step if end - start >= step else (end - start)
    return out
