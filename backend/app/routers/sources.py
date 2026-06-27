from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .. import repositories as repo
from ..schemas import Source, SourceCreateText, SourceCreateUrl, SourceDetail
from ..services import ingestion

router = APIRouter(prefix="/api/notebooks/{notebook_id}/sources", tags=["sources"])


def _require_notebook(notebook_id: str):
    if not repo.get_notebook(notebook_id):
        raise HTTPException(404, "Notebook not found")


@router.get("", response_model=list[Source])
def list_sources(notebook_id: str):
    _require_notebook(notebook_id)
    return repo.list_sources(notebook_id)


@router.post("/text", response_model=Source, status_code=201)
def add_text(notebook_id: str, body: SourceCreateText):
    _require_notebook(notebook_id)
    return ingestion.ingest_text(notebook_id, body.title, body.content)


@router.post("/url", response_model=Source, status_code=201)
def add_url(notebook_id: str, body: SourceCreateUrl):
    _require_notebook(notebook_id)
    try:
        return ingestion.ingest_url(notebook_id, body.url, body.title)
    except Exception as exc:  # network / parse failure -> 422 with reason
        raise HTTPException(422, f"Could not import URL: {exc}")


@router.post("/file", response_model=Source, status_code=201)
async def add_file(notebook_id: str, file: UploadFile = File(...)):
    _require_notebook(notebook_id)
    data = await file.read()
    if not data:
        raise HTTPException(422, "Empty file")
    try:
        return ingestion.ingest_file(notebook_id, file.filename or "upload", data)
    except Exception as exc:
        raise HTTPException(422, f"Could not import file: {exc}")


@router.get("/{source_id}", response_model=SourceDetail)
def get_source(notebook_id: str, source_id: str):
    _require_notebook(notebook_id)
    src = repo.get_source(source_id)
    if not src or src["notebook_id"] != notebook_id:
        raise HTTPException(404, "Source not found")
    return src


@router.delete("/{source_id}", status_code=204)
def delete_source(notebook_id: str, source_id: str):
    _require_notebook(notebook_id)
    src = repo.get_source(source_id)
    if not src or src["notebook_id"] != notebook_id:
        raise HTTPException(404, "Source not found")
    repo.delete_source(source_id)
