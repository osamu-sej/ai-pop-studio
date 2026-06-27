import pytest


@pytest.mark.parametrize(
    "kind", ["summary", "study_guide", "faq", "timeline", "key_topics", "briefing", "mindmap"]
)
def test_transformations_produce_notes(client, notebook_with_source, kind):
    nid = notebook_with_source["id"]
    res = client.post(
        f"/api/notebooks/{nid}/studio/transform",
        json={"kind": kind, "save_as_note": True},
    ).json()
    assert res["kind"] == kind
    assert len(res["content"]) > 0
    assert res["note_id"] is not None

    notes = client.get(f"/api/notebooks/{nid}/notes").json()
    assert any(n["id"] == res["note_id"] and n["note_type"] == "generated" for n in notes)


def test_podcast_generation(client, notebook_with_source):
    nid = notebook_with_source["id"]
    pod = client.post(
        f"/api/notebooks/{nid}/studio/podcasts",
        json={"style": "conversational", "length": "short"},
    ).json()
    assert pod["status"] == "ready"
    assert "🎙️" in pod["transcript"] or "Welcome" in pod["transcript"]

    listing = client.get(f"/api/notebooks/{nid}/studio/podcasts").json()
    assert any(p["id"] == pod["id"] for p in listing)


def test_notes_crud(client, notebook):
    nid = notebook["id"]
    note = client.post(f"/api/notebooks/{nid}/notes", json={"title": "T", "content": "C"}).json()
    updated = client.patch(
        f"/api/notebooks/{nid}/notes/{note['id']}", json={"content": "C2"}
    ).json()
    assert updated["content"] == "C2"
    assert client.delete(f"/api/notebooks/{nid}/notes/{note['id']}").status_code == 204


def test_status_endpoint(client):
    s = client.get("/api/status").json()
    assert s["llm_mode"] in {"model", "heuristic"}
    assert "embedding_provider" in s


def test_suggestions(client, notebook_with_source):
    nid = notebook_with_source["id"]
    qs = client.get(f"/api/notebooks/{nid}/chat/suggestions").json()
    assert isinstance(qs, list) and len(qs) >= 1
    assert all(isinstance(q, str) and q for q in qs)


def test_suggestions_empty_without_sources(client, notebook):
    qs = client.get(f"/api/notebooks/{notebook['id']}/chat/suggestions").json()
    assert qs == []


def test_export_markdown(client, notebook_with_source):
    nid = notebook_with_source["id"]
    # add a note + a chat turn so the export covers all sections
    client.post(f"/api/notebooks/{nid}/notes", json={"title": "My note", "content": "hello"})
    client.post(f"/api/notebooks/{nid}/chat", json={"message": "Summarize please"})
    resp = client.get(f"/api/notebooks/{nid}/export")
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("content-disposition", "")
    body = resp.text
    assert "## Sources" in body
    assert "Renewables" in body
    assert "My note" in body
    assert "## Conversation" in body
