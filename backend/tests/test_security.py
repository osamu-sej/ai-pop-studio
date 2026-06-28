import pytest


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",       # non-http scheme
        "ftp://example.com/x",      # non-http scheme
        "http://127.0.0.1:8000/",   # loopback
        "http://169.254.169.254/",  # link-local (cloud metadata)
        "http://0.0.0.0/",          # unspecified
    ],
)
def test_url_ingestion_rejects_unsafe(client, notebook, url):
    # SSRF guard runs before any network call, so this is deterministic/offline.
    resp = client.post(f"/api/notebooks/{notebook['id']}/sources/url", json={"url": url})
    assert resp.status_code == 422, f"{url} should be rejected"


def test_upload_size_limit(client, notebook):
    from app.config import get_settings

    s = get_settings()
    original = s.max_upload_mb
    s.max_upload_mb = 0  # make any non-empty upload exceed the limit
    try:
        resp = client.post(
            f"/api/notebooks/{notebook['id']}/sources/file",
            files={"file": ("big.txt", b"some bytes that exceed zero", "text/plain")},
        )
        assert resp.status_code == 413
    finally:
        s.max_upload_mb = original
