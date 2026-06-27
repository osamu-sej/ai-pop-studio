from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .. import repositories as repo
from ..schemas import NotebookGuide, Podcast, TransformRequest, TransformResult
from ..schemas import PodcastRequest
from ..services import studio as studio_service

router = APIRouter(prefix="/api/notebooks/{notebook_id}/studio", tags=["studio"])


def _require_notebook(notebook_id: str):
    if not repo.get_notebook(notebook_id):
        raise HTTPException(404, "Notebook not found")


# ── Notebook guide (auto overview) ─────────────────────────────────────────
@router.get("/guide", response_model=NotebookGuide)
def guide(notebook_id: str):
    _require_notebook(notebook_id)
    return studio_service.notebook_guide(notebook_id)


# ── Transformations (summary, study guide, FAQ, ...) ───────────────────────
@router.post("/transform", response_model=TransformResult)
def transform(notebook_id: str, body: TransformRequest):
    _require_notebook(notebook_id)
    return studio_service.run_transformation(
        notebook_id, body.kind, body.source_ids, body.save_as_note
    )


# ── Podcast / audio overview ───────────────────────────────────────────────
def _to_podcast_model(p: dict) -> dict:
    audio_url = None
    if p.get("audio_path"):
        audio_url = f"/api/notebooks/{p['notebook_id']}/studio/podcasts/{p['id']}/audio"
    return {**p, "audio_url": audio_url}


@router.get("/podcasts", response_model=list[Podcast])
def list_podcasts(notebook_id: str):
    _require_notebook(notebook_id)
    return [_to_podcast_model(p) for p in repo.list_podcasts(notebook_id)]


@router.post("/podcasts", response_model=Podcast)
def create_podcast(notebook_id: str, body: PodcastRequest):
    _require_notebook(notebook_id)
    p = studio_service.generate_podcast(notebook_id, body)
    return _to_podcast_model(p)


@router.get("/podcasts/{podcast_id}/audio")
def get_podcast_audio(notebook_id: str, podcast_id: str):
    p = repo.get_podcast(podcast_id)
    if not p or p["notebook_id"] != notebook_id or not p.get("audio_path"):
        raise HTTPException(404, "Audio not available")
    return FileResponse(p["audio_path"], media_type="audio/wav",
                        filename=f"{p['title']}.wav")


@router.delete("/podcasts/{podcast_id}", status_code=204)
def delete_podcast(notebook_id: str, podcast_id: str):
    p = repo.get_podcast(podcast_id)
    if not p or p["notebook_id"] != notebook_id:
        raise HTTPException(404, "Podcast not found")
    repo.delete_podcast(podcast_id)
