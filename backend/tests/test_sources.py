import fitz  # PyMuPDF


def test_add_text_source(client, notebook):
    nid = notebook["id"]
    src = client.post(
        f"/api/notebooks/{nid}/sources/text",
        json={"title": "Note A", "content": "The quick brown fox jumps over the lazy dog."},
    ).json()
    assert src["source_type"] == "text"
    assert src["token_count"] > 0

    sources = client.get(f"/api/notebooks/{nid}/sources").json()
    assert len(sources) == 1

    detail = client.get(f"/api/notebooks/{nid}/sources/{src['id']}").json()
    assert "quick brown fox" in detail["content"]

    assert client.delete(f"/api/notebooks/{nid}/sources/{src['id']}").status_code == 204
    assert client.get(f"/api/notebooks/{nid}/sources").json() == []


def test_add_pdf_source(client, notebook):
    nid = notebook["id"]
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Aurora test document about renewable solar energy systems.")
    data = doc.tobytes()
    doc.close()

    resp = client.post(
        f"/api/notebooks/{nid}/sources/file",
        files={"file": ("test.pdf", data, "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    src = resp.json()
    assert src["source_type"] == "pdf"
    assert "solar energy" in client.get(
        f"/api/notebooks/{nid}/sources/{src['id']}"
    ).json()["content"]


def test_source_count_reflected_on_notebook(client, notebook):
    nid = notebook["id"]
    client.post(f"/api/notebooks/{nid}/sources/text", json={"title": "x", "content": "hello world"})
    assert client.get(f"/api/notebooks/{nid}").json()["source_count"] == 1


def test_reindex_source(client, notebook):
    nid = notebook["id"]
    src = client.post(
        f"/api/notebooks/{nid}/sources/text",
        json={"title": "T", "content": "Solar panels and wind power generate clean electricity."},
    ).json()
    resp = client.post(f"/api/notebooks/{nid}/sources/{src['id']}/reindex")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
    # retrieval still works after reindexing
    hits = client.post(f"/api/notebooks/{nid}/search", json={"query": "solar"}).json()
    assert len(hits) >= 1


def test_audio_upload_filename_is_sanitised(client, notebook):
    # A malicious filename must never become a filesystem path (traversal guard).
    nid = notebook["id"]
    resp = client.post(
        f"/api/notebooks/{nid}/sources/file",
        files={"file": ("../../../etc/evil.mp3", b"not-real-audio", "audio/mpeg")},
    )
    assert resp.status_code == 201, resp.text
    src = resp.json()
    assert ".." not in src["origin"]
    assert src["origin"] == "evil.mp3"
