"""Hybrid retrieval: blend semantic (vector) and lexical (keyword) scores.

Combining both is what makes NotebookLM-style grounding robust — vectors catch
paraphrase/meaning, keywords catch exact names/numbers/acronyms that embeddings
sometimes wash out.
"""

from __future__ import annotations

import math
from collections import Counter

import numpy as np

from .. import repositories as repo
from ..ai.embeddings import get_embedder
from ..ai.heuristics import tokenize


def _bm25ish(query: str, chunks: list[dict]) -> dict[str, float]:
    """Lightweight BM25 over the candidate chunk set, keyed by chunk id."""
    q_terms = [t for t in tokenize(query) if len(t) > 1]
    if not q_terms or not chunks:
        return {}
    docs = {c["id"]: tokenize(c["text"]) for c in chunks}
    n = len(docs)
    avgdl = sum(len(d) for d in docs.values()) / max(1, n)
    df: Counter = Counter()
    for terms in docs.values():
        for t in set(terms):
            df[t] += 1
    k1, b = 1.5, 0.75
    scores: dict[str, float] = {}
    for cid, terms in docs.items():
        tf = Counter(terms)
        dl = len(terms)
        score = 0.0
        for t in q_terms:
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            denom = tf[t] + k1 * (1 - b + b * dl / avgdl)
            score += idf * (tf[t] * (k1 + 1)) / denom
        if score:
            scores[cid] = score
    return scores


def _semantic(query: str, chunks: list[dict]) -> dict[str, float]:
    vecs = [c for c in chunks if c.get("vector") is not None]
    if not vecs:
        return {}
    qvec = get_embedder().embed([query])[0]
    matrix = np.vstack([c["vector"] for c in vecs])
    sims = matrix @ qvec  # vectors are L2-normalised -> dot == cosine
    return {c["id"]: float(s) for c, s in zip(vecs, sims)}


def _normalise(d: dict[str, float]) -> dict[str, float]:
    if not d:
        return {}
    hi = max(d.values())
    if hi <= 0:
        return {k: 0.0 for k in d}
    return {k: v / hi for k, v in d.items()}


def rank(query: str, chunks: list[dict], top_k: int, alpha: float = 0.6) -> list[tuple[dict, float]]:
    """Hybrid-rank a candidate chunk list. alpha weights semantic vs lexical."""
    if not chunks:
        return []
    by_id = {c["id"]: c for c in chunks}
    lex = _normalise(_bm25ish(query, chunks))
    sem = _normalise(_semantic(query, chunks))
    combined: dict[str, float] = {}
    for cid in set(lex) | set(sem):
        combined[cid] = alpha * sem.get(cid, 0.0) + (1 - alpha) * lex.get(cid, 0.0)
    ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [(by_id[cid], score) for cid, score in ranked]


def hybrid_search(notebook_id: str, query: str, top_k: int = 8,
                  source_ids: list[str] | None = None,
                  alpha: float = 0.6) -> list[dict]:
    chunks = repo.get_chunks_for_notebook(notebook_id, source_ids)
    return [
        {
            "source_id": c["source_id"],
            "source_title": c["source_title"],
            "chunk_idx": c["idx"],
            "text": c["text"],
            "score": round(float(score), 4),
        }
        for c, score in rank(query, chunks, top_k, alpha)
    ]


def global_search(query: str, top_k: int = 20, alpha: float = 0.6) -> list[dict]:
    """Search across every notebook at once."""
    chunks = repo.get_chunks_global()
    return [
        {
            "notebook_id": c["notebook_id"],
            "notebook_name": c["notebook_name"],
            "notebook_emoji": c["notebook_emoji"],
            "source_id": c["source_id"],
            "source_title": c["source_title"],
            "chunk_idx": c["idx"],
            "text": c["text"],
            "score": round(float(score), 4),
        }
        for c, score in rank(query, chunks, top_k, alpha)
    ]
