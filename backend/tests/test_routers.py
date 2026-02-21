"""ルーターの基本的なAPIテスト"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_health(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_templates_list(client: AsyncClient):
    response = await client.get("/api/templates")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert isinstance(data["templates"], list)


@pytest.mark.anyio
async def test_pdf_parse_rejects_non_pdf(client: AsyncClient):
    response = await client.post(
        "/api/pdf/parse",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_pdf_parse_rejects_empty(client: AsyncClient):
    response = await client.post(
        "/api/pdf/parse",
        files={"file": ("test.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_pop_generate_rejects_empty_products(client: AsyncClient):
    response = await client.post(
        "/api/pop/generate",
        json={"template_id": "new_pop_np", "products": []},
    )
    assert response.status_code == 400
