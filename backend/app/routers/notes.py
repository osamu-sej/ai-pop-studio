from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import repositories as repo
from ..schemas import Note, NoteCreate, NoteUpdate

router = APIRouter(prefix="/api/notebooks/{notebook_id}/notes", tags=["notes"])


def _require_notebook(notebook_id: str):
    if not repo.get_notebook(notebook_id):
        raise HTTPException(404, "Notebook not found")


@router.get("", response_model=list[Note])
def list_notes(notebook_id: str):
    _require_notebook(notebook_id)
    return repo.list_notes(notebook_id)


@router.post("", response_model=Note, status_code=201)
def create_note(notebook_id: str, body: NoteCreate):
    _require_notebook(notebook_id)
    return repo.create_note(notebook_id, body.title, body.content)


@router.patch("/{note_id}", response_model=Note)
def update_note(notebook_id: str, note_id: str, body: NoteUpdate):
    _require_notebook(notebook_id)
    note = repo.get_note(note_id)
    if not note or note["notebook_id"] != notebook_id:
        raise HTTPException(404, "Note not found")
    return repo.update_note(note_id, title=body.title, content=body.content)


@router.delete("/{note_id}", status_code=204)
def delete_note(notebook_id: str, note_id: str):
    _require_notebook(notebook_id)
    note = repo.get_note(note_id)
    if not note or note["notebook_id"] != notebook_id:
        raise HTTPException(404, "Note not found")
    repo.delete_note(note_id)
