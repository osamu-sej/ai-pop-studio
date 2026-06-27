"""Hybrid retrieval: blend semantic (vector) and lexical (keyword) scores.

Combining both is what makes NotebookLM-style grounding robust — vectors catch
paraphrase/meaning, keywords catch exact names/numbers/acronyms that embeddings
sometimes wash out.
"""

from __future__ import annotations

import math
from collections import Counter

from .. import repositories as repo
from ..ai.heuristics import tokenize
from . import vectorstore


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


def _normalise(d: dict[str, float]) -> dict[str, float]:
    if not d:
        return {}
    hi = max(d.values())
    if hi <= 0:
        return {k: 0.0 for k in d}
    return {k: v / hi for k, v in d.items()}


def hybrid_search(notebook_id: str, query: str, top_k: int = 8,
                  source_ids: list[str] | None = None,
                  alpha: float = 0.6) -> list[dict]:
    """alpha weights the semantic score; (1-alpha) weights the lexical score."""
    chunks = repo.get_chunks_for_notebook(notebook_id, source_ids)
    if not chunks:
        return []
    by_id = {c["id"]: c for c in chunks}

    # lexical
    lex = _normalise(_bm25ish(query, chunks))

    # semantic
    vec_hits = vectorstore.vector_search(notebook_id, query, top_k=top_k * 3,
                                         source_ids=source_ids)
    # map vector hits back onto chunk ids
    vid_by_key = {(c["source_id"], c["idx"]): c["id"] for c in chunks}
    sem_raw = {}
    for h in vec_hits:
        cid = vid_by_key.get((h["source_id"], h["chunk_idx"]))
        if cid:
            sem_raw[cid] = h["score"]
    sem = _normalise(sem_raw)

    combined: dict[str, float] = {}
    for cid in set(lex) | set(sem):
        combined[cid] = alpha * sem.get(cid, 0.0) + (1 - alpha) * lex.get(cid, 0.0)

    ranked = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    out = []
    for cid, score in ranked:
        c = by_id[cid]
        out.append({
            "source_id": c["source_id"],
            "source_title": c["source_title"],
            "chunk_idx": c["idx"],
            "text": c["text"],
            "score": round(float(score), 4),
        })
    return out
