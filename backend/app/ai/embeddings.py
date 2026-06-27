"""Embedding providers for semantic search.

Three tiers, all API-free:

1. **Ollama** (`nomic-embed-text`) — best quality, local, free.
2. **sentence-transformers** — great quality, local, free (optional install).
3. **Hashing** — pure-python fallback with *zero* dependencies beyond numpy.
   Uses signed feature hashing over word + character n-grams. It captures
   lexical/morphological overlap well enough to make vector retrieval useful
   even on a machine with no AI models installed at all.

`provider="auto"` probes 1 → 2 → 3 and uses the first that works.
"""

from __future__ import annotations

import hashlib
import re

import httpx
import numpy as np

from ..config import get_settings

_WORD = re.compile(r"\w+", re.UNICODE)


class BaseEmbedder:
    name = "none"
    dim = 0

    def available(self) -> bool:  # pragma: no cover - interface
        return False

    def embed(self, texts: list[str]) -> list[np.ndarray]:  # pragma: no cover
        raise NotImplementedError


class HashingEmbedder(BaseEmbedder):
    """Deterministic, dependency-light fallback. Always available."""

    name = "hashing"

    def __init__(self, dim: int = 384):
        self.dim = dim

    def available(self) -> bool:
        return True

    def _features(self, text: str):
        text = text.lower()
        words = _WORD.findall(text)
        # whole words
        for w in words:
            yield w, 1.0
        # word bigrams (captures short phrases)
        for a, b in zip(words, words[1:]):
            yield f"{a}_{b}", 0.7
        # character 3-grams over the joined token stream (morphology / typos)
        joined = " ".join(words)
        for i in range(len(joined) - 2):
            yield "#" + joined[i:i + 3], 0.3

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        out = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            for token, weight in self._features(text):
                h = int.from_bytes(hashlib.md5(token.encode("utf-8")).digest()[:8], "little")
                idx = h % self.dim
                sign = 1.0 if (h >> 63) & 1 else -1.0
                vec[idx] += sign * weight
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec /= norm
            out.append(vec)
        return out


class OllamaEmbedder(BaseEmbedder):
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dim = 0

    def available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            if r.status_code != 200:
                return False
            names = [m.get("name", "") for m in r.json().get("models", [])]
            return any(self.model.split(":")[0] in n for n in names)
        except Exception:
            return False

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        out = []
        for text in texts:
            r = httpx.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=60.0,
            )
            r.raise_for_status()
            vec = np.asarray(r.json()["embedding"], dtype=np.float32)
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec /= norm
            self.dim = vec.shape[0]
            out.append(vec)
        return out


class SentenceTransformerEmbedder(BaseEmbedder):
    name = "sentence-transformers"

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self.dim = 0

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # lazy, optional

            self._model = SentenceTransformer(self.model_name)
            self.dim = self._model.get_sentence_embedding_dimension()
        return self._model

    def available(self) -> bool:
        try:
            import importlib.util

            return importlib.util.find_spec("sentence_transformers") is not None
        except Exception:
            return False

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        model = self._load()
        vecs = model.encode(texts, normalize_embeddings=True)
        return [np.asarray(v, dtype=np.float32) for v in vecs]


def build_embedder() -> BaseEmbedder:
    s = get_settings()
    provider = (s.embedding_provider or "auto").lower()
    candidates: list[BaseEmbedder]
    if provider == "ollama":
        candidates = [OllamaEmbedder(s.llm_base_url, s.embedding_model)]
    elif provider in {"sentence-transformers", "st"}:
        candidates = [SentenceTransformerEmbedder(s.st_embedding_model)]
    elif provider == "hashing":
        candidates = [HashingEmbedder(s.embedding_dim_fallback)]
    else:  # auto
        candidates = [
            OllamaEmbedder(s.llm_base_url, s.embedding_model),
            SentenceTransformerEmbedder(s.st_embedding_model),
        ]
    for emb in candidates:
        try:
            if emb.available():
                return emb
        except Exception:
            continue
    return HashingEmbedder(s.embedding_dim_fallback)


_cached: BaseEmbedder | None = None


def get_embedder(refresh: bool = False) -> BaseEmbedder:
    global _cached
    if _cached is None or refresh:
        _cached = build_embedder()
    return _cached
