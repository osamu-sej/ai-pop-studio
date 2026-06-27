"""In-process vector search over a notebook's chunks (numpy cosine)."""

from __future__ import annotations

import numpy as np

from .. import repositories as repo
from ..ai.embeddings import get_embedder


def embed_chunks(texts: list[str]) -> list[np.ndarray]:
    if not texts:
        return []
    return get_embedder().embed(texts)


def vector_search(notebook_id: str, query: str, top_k: int,
                  source_ids: list[str] | None = None) -> list[dict]:
    chunks = repo.get_chunks_for_notebook(notebook_id, source_ids)
    vectors = [c for c in chunks if c.get("vector") is not None]
    if not vectors:
        return []
    qvec = get_embedder().embed([query])[0]
    matrix = np.vstack([c["vector"] for c in vectors])
    # vectors are L2-normalised at write time -> dot product == cosine similarity
    sims = matrix @ qvec
    order = np.argsort(-sims)[:top_k]
    results = []
    for i in order:
        c = vectors[int(i)]
        results.append({
            "source_id": c["source_id"],
            "source_title": c["source_title"],
            "chunk_idx": c["idx"],
            "text": c["text"],
            "score": float(sims[int(i)]),
        })
    return results
