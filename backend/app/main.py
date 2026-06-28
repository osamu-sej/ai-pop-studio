"""Aurora Notebook — FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import get_settings
from .database import init_db
from .routers import chat, notebooks, notes, search, sources, studio, system

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings().ensure_dirs()
    init_db()
    yield


app = FastAPI(
    title="Aurora Notebook",
    description="A local-first, API-free alternative to Google NotebookLM.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    # The app uses no cookies/credentials; keeping this False keeps a wildcard
    # origin spec valid per the CORS spec.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (system, notebooks, sources, notes, chat, search, studio):
    app.include_router(r.router)


# ── Serve the built SPA in production (if `frontend/dist` exists) ───────────
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        # Unknown API paths must 404 as JSON, not fall through to the SPA shell.
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        # Serve a real static file only if it resolves *inside* the dist dir
        # (guards against path traversal like `../../etc/passwd`).
        if full_path:
            candidate = (FRONTEND_DIST / full_path).resolve()
            root = FRONTEND_DIST.resolve()
            if candidate.is_file() and candidate.is_relative_to(root):
                return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "app": "Aurora Notebook",
            "version": __version__,
            "docs": "/docs",
            "note": "Frontend not built yet — run `npm run build` in /frontend, "
                    "or use the Vite dev server.",
        }
