"""Embedding helper used at ingest time.

Similarity search itself lives in `search.py` (numpy cosine + BM25), operating
over chunk vectors stored inline in SQLite.
"""

from __future__ import annotations

import numpy as np

from ..ai.embeddings import get_embedder


def embed_chunks(texts: list[str]) -> list[np.ndarray]:
    if not texts:
        return []
    return get_embedder().embed(texts)
