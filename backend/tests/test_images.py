"""画像生成・保管・弁当レイアウトAPIのテスト。"""

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# backend/ を import パスに追加
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """storage をテンポラリディレクトリに差し替えたクライアント。"""
    import services.storage as storage

    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(storage, "IMAGES_DIR", tmp_path / "images")
    monkeypatch.setattr(storage, "IMAGES_META", tmp_path / "images.json")
    monkeypatch.setattr(storage, "BENTO_FILE", tmp_path / "bento.json")

    # main を再読み込みして差し替え後の IMAGES_DIR を使わせる
    import main
    importlib.reload(main)
    return TestClient(main.app)


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_generate_and_list(client):
    res = client.post("/api/images/generate", json={"prompt": "焼き鮭"})
    assert res.status_code == 200
    body = res.json()
    assert body["prompt"] == "焼き鮭"
    assert body["url"].startswith("/media/images/")
    assert "id" in body

    lst = client.get("/api/images")
    assert lst.status_code == 200
    images = lst.json()["images"]
    assert len(images) == 1
    assert images[0]["id"] == body["id"]


def test_generate_rejects_empty_prompt(client):
    res = client.post("/api/images/generate", json={"prompt": "   "})
    assert res.status_code == 422 or res.status_code == 400


def test_generated_image_is_served(client):
    res = client.post("/api/images/generate", json={"prompt": "唐揚げ"})
    url = res.json()["url"]
    img = client.get(url)
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/png"
    assert img.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_delete_image(client):
    res = client.post("/api/images/generate", json={"prompt": "卵焼き"})
    image_id = res.json()["id"]

    dele = client.delete(f"/api/images/{image_id}")
    assert dele.status_code == 200

    lst = client.get("/api/images")
    assert lst.json()["images"] == []

    missing = client.delete(f"/api/images/{image_id}")
    assert missing.status_code == 404


def test_bento_save_and_get(client):
    gen = client.post("/api/images/generate", json={"prompt": "ご飯"})
    image_id = gen.json()["id"]

    put = client.put(
        "/api/bento",
        json={"preset": "makunouchi", "compartments": {"rice": image_id, "main": None}},
    )
    assert put.status_code == 200
    # None の仕切りは保存されない
    assert put.json()["compartments"] == {"rice": image_id}
    assert put.json()["preset"] == "makunouchi"

    get = client.get("/api/bento")
    assert get.json()["compartments"] == {"rice": image_id}
    assert get.json()["preset"] == "makunouchi"


def test_bento_default_has_preset_key(client):
    # 未保存でも preset キーを含む
    get = client.get("/api/bento")
    assert get.json()["preset"] is None
    assert get.json()["compartments"] == {}


def test_deleting_image_clears_bento_slot(client):
    gen = client.post("/api/images/generate", json={"prompt": "煮物"})
    image_id = gen.json()["id"]
    client.put(
        "/api/bento",
        json={"preset": "makunouchi", "compartments": {"side1": image_id}},
    )

    client.delete(f"/api/images/{image_id}")
    get = client.get("/api/bento")
    assert get.json()["compartments"] == {}
