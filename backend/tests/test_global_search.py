def test_global_search_across_notebooks(client):
    a = client.post("/api/notebooks", json={"name": "Energy"}).json()
    b = client.post("/api/notebooks", json={"name": "Cooking"}).json()
    client.post(
        f"/api/notebooks/{a['id']}/sources/text",
        json={"title": "Solar", "content": "Photovoltaic solar panels convert sunlight to electricity."},
    )
    client.post(
        f"/api/notebooks/{b['id']}/sources/text",
        json={"title": "Pasta", "content": "Boil the pasta in salted water until al dente."},
    )

    hits = client.post("/api/search", json={"query": "solar electricity", "top_k": 5}).json()
    assert len(hits) >= 1
    top = hits[0]
    assert top["notebook_id"] == a["id"]
    assert top["notebook_name"] == "Energy"
    assert "solar" in top["text"].lower()

    # a clearly cooking query should rank the cooking notebook first
    hits2 = client.post("/api/search", json={"query": "boil pasta water"}).json()
    assert hits2 and hits2[0]["notebook_id"] == b["id"]

    client.delete(f"/api/notebooks/{a['id']}")
    client.delete(f"/api/notebooks/{b['id']}")


def test_global_search_empty(client):
    # no notebooks/sources guaranteed empty result is fine (other tests may add some)
    hits = client.post("/api/search", json={"query": "zzz-nonexistent-term-xyzzy"}).json()
    assert isinstance(hits, list)
