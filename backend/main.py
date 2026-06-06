import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import images, bento
from services.storage import IMAGES_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="Bento Composer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router, prefix="/api/images", tags=["Images"])
app.include_router(bento.router, prefix="/api/bento", tags=["Bento"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 生成画像を配信（storage/images/ -> /media/images/）
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/images", StaticFiles(directory=IMAGES_DIR), name="media-images")


# 本番環境: ビルド済みフロントエンドを配信
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPAのフォールバック: 全パスをindex.htmlに転送"""
        return FileResponse(FRONTEND_DIR / "index.html")
