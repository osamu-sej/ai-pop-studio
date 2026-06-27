def test_create_list_get_update_delete(client):
    created = client.post("/api/notebooks", json={"name": "My NB", "emoji": "📚"}).json()
    nid = created["id"]
    assert created["name"] == "My NB"
    assert created["source_count"] == 0

    listing = client.get("/api/notebooks").json()
    assert any(nb["id"] == nid for nb in listing)

    got = client.get(f"/api/notebooks/{nid}")
    assert got.status_code == 200
    assert got.json()["emoji"] == "📚"

    patched = client.patch(f"/api/notebooks/{nid}", json={"name": "Renamed"}).json()
    assert patched["name"] == "Renamed"

    assert client.delete(f"/api/notebooks/{nid}").status_code == 204
    assert client.get(f"/api/notebooks/{nid}").status_code == 404


def test_missing_notebook_404(client):
    assert client.get("/api/notebooks/does-not-exist").status_code == 404
