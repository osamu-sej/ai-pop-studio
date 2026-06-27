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
