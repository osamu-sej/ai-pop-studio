import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import pdf, pop, templates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="POP Generator API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF"])
app.include_router(pop.router, prefix="/api/pop", tags=["POP"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 本番環境: ビルド済みフロントエンドを配信
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPAのフォールバック: 全パスをindex.htmlに転送"""
        return FileResponse(FRONTEND_DIR / "index.html")
