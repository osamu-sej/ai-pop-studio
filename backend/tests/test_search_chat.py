def test_search_returns_relevant_chunk(client, notebook_with_source):
    nid = notebook_with_source["id"]
    hits = client.post(
        f"/api/notebooks/{nid}/search",
        json={"query": "cost of solar panels", "top_k": 3},
    ).json()
    assert len(hits) >= 1
    # the cheapest-panels sentence should surface near the top
    joined = " ".join(h["text"] for h in hits).lower()
    assert "photovoltaic" in joined or "panels" in joined


def test_chat_answers_with_citations(client, notebook_with_source):
    nid = notebook_with_source["id"]
    reply = client.post(
        f"/api/notebooks/{nid}/chat",
        json={"message": "What happened to the cost of photovoltaic panels?"},
    ).json()
    assert reply["role"] == "assistant"
    assert len(reply["content"]) > 0
    assert len(reply["citations"]) >= 1
    assert reply["citations"][0]["source_title"] == "Renewables"

    history = client.get(f"/api/notebooks/{nid}/chat").json()
    # user message + assistant reply persisted
    assert [m["role"] for m in history][-2:] == ["user", "assistant"]

    assert client.delete(f"/api/notebooks/{nid}/chat").status_code == 204
    assert client.get(f"/api/notebooks/{nid}/chat").json() == []


def test_chat_without_sources_is_graceful(client, notebook):
    nid = notebook["id"]
    reply = client.post(f"/api/notebooks/{nid}/chat", json={"message": "Hello?"}).json()
    assert reply["role"] == "assistant"
    assert reply["citations"] == []


def test_chat_streaming(client, notebook_with_source):
    import json

    nid = notebook_with_source["id"]
    tokens, done = [], None
    with client.stream(
        "POST",
        f"/api/notebooks/{nid}/chat/stream",
        json={"message": "What about battery storage?"},
    ) as r:
        assert r.status_code == 200
        for line in r.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            evt = json.loads(line[len("data:"):].strip())
            if evt["type"] == "token":
                tokens.append(evt["text"])
            elif evt["type"] == "done":
                done = evt["message"]

    assert tokens, "expected streamed token events"
    assert done is not None
    assert done["role"] == "assistant"
    assert "".join(tokens).strip() == done["content"].strip()
    # streamed reply is also persisted exactly once
    history = client.get(f"/api/notebooks/{nid}/chat").json()
    assert [m["role"] for m in history][-2:] == ["user", "assistant"]
