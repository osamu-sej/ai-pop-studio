"""Pytest fixtures.

Force the fully-offline path (heuristic LLM + hashing embeddings) so the suite
runs anywhere with no models, no network and no API keys.
"""

import os
import tempfile

os.environ.setdefault("AURORA_DATA_DIR", tempfile.mkdtemp(prefix="aurora_test_"))
os.environ.setdefault("AURORA_LLM_PROVIDER", "heuristic")
os.environ.setdefault("AURORA_EMBEDDING_PROVIDER", "hashing")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

SAMPLE = (
    "Solar power capacity grew rapidly between 2010 and 2023. "
    "In 2015 the cost of photovoltaic panels fell by sixty percent, a major milestone. "
    "Wind energy expanded too, especially offshore wind farms across Europe. "
    "Battery storage became dramatically cheaper in 2020, improving grid stability. "
    "By 2023 renewables supplied a record share of global electricity. "
    "Critics note that intermittency remains a challenge for both solar and wind."
)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def notebook(client):
    nb = client.post("/api/notebooks", json={"name": "Test Notebook", "emoji": "🧪"}).json()
    yield nb
    client.delete(f"/api/notebooks/{nb['id']}")


@pytest.fixture
def notebook_with_source(client, notebook):
    client.post(
        f"/api/notebooks/{notebook['id']}/sources/text",
        json={"title": "Renewables", "content": SAMPLE},
    )
    return notebook
