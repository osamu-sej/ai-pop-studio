import numpy as np

from app.ai.embeddings import HashingEmbedder
from app.ai.heuristics import summarize, top_keywords
from app.services.chunking import chunk_text
from app.services.search import rank


def test_rank_tolerates_mixed_dimension_vectors():
    # Simulates the embedding model being changed after some sources were
    # indexed: stored vectors have different dims. Ranking must not crash.
    a = np.random.rand(384).astype("float32")
    a /= np.linalg.norm(a)
    b = np.random.rand(128).astype("float32")
    b /= np.linalg.norm(b)
    chunks = [
        {"id": "1", "text": "solar energy photovoltaic panels", "vector": a},
        {"id": "2", "text": "boil pasta in salted water", "vector": b},
    ]
    results = rank("solar energy panels", chunks, top_k=2)
    assert isinstance(results, list)
    assert any(c["id"] == "1" for c, _ in results)


def test_chunking_overlap_and_size():
    text = "\n\n".join(f"Paragraph number {i} with some words." for i in range(60))
    chunks = chunk_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 400 for c in chunks)  # generous upper bound incl. overlap


def test_chunking_short_text_single_chunk():
    assert chunk_text("hello world", 1000, 100) == ["hello world"]


def test_hashing_embeddings_similarity():
    emb = HashingEmbedder(dim=256)
    a, b, c = emb.embed([
        "solar panels and photovoltaic energy",
        "photovoltaic solar panel energy systems",
        "the history of medieval european castles",
    ])
    sim_ab = float(np.dot(a, b))
    sim_ac = float(np.dot(a, c))
    assert sim_ab > sim_ac  # related texts are closer than unrelated ones


def test_summarize_shortens():
    text = " ".join(f"Sentence {i} about climate and energy policy details." for i in range(20))
    summary = summarize(text, max_sentences=3)
    assert 0 < len(summary) < len(text)


def test_top_keywords_extraction():
    text = "Solar energy solar power renewable energy battery storage grid."
    kws = top_keywords(text, 5)
    assert "solar" in kws or "energy" in kws
