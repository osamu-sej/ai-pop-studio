def test_settings_roundtrip(client):
    view = client.get("/api/settings").json()
    # conftest forces the offline path via env
    assert view["llm_provider"] == "heuristic"
    assert view["llm_api_key_set"] is False

    status = client.put(
        "/api/settings",
        json={"llm_base_url": "http://localhost:11434", "llm_model": "qwen2.5:7b"},
    ).json()
    assert status["llm_mode"] in {"model", "heuristic"}

    view2 = client.get("/api/settings").json()
    assert view2["llm_model"] == "qwen2.5:7b"
    assert view2["llm_base_url"] == "http://localhost:11434"
    # provider untouched -> still heuristic, so the rest of the suite is unaffected
    assert view2["llm_provider"] == "heuristic"


def test_status_reflects_override(client):
    try:
        st = client.put(
            "/api/settings", json={"llm_provider": "ollama", "llm_model": "qwen2.5:7b"}
        ).json()
        assert st["llm_provider"] == "ollama"
        assert st["llm_model"] == "qwen2.5:7b"
        # no Ollama server in CI -> can't connect -> heuristic mode, reported honestly
        assert st["llm_mode"] == "heuristic"
    finally:
        client.put("/api/settings", json={"llm_provider": "heuristic"})


def test_api_key_never_returned(client):
    client.put("/api/settings", json={"llm_api_key": "secret-should-not-leak"})
    view = client.get("/api/settings").json()
    assert "llm_api_key" not in view
    assert view["llm_api_key_set"] is True
    # clean up so other tests see no key
    client.put("/api/settings", json={"llm_api_key": ""})
