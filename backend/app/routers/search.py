from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import repositories as repo
from ..schemas import SearchHit, SearchRequest
from ..services import search as search_service

router = APIRouter(prefix="/api/notebooks/{notebook_id}/search", tags=["search"])


@router.post("", response_model=list[SearchHit])
def search(notebook_id: str, body: SearchRequest):
    if not repo.get_notebook(notebook_id):
        raise HTTPException(404, "Notebook not found")
    return search_service.hybrid_search(
        notebook_id, body.query, top_k=body.top_k, source_ids=body.source_ids
    )
