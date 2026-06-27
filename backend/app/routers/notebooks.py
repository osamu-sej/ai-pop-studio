from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import repositories as repo
from ..schemas import Notebook, NotebookCreate, NotebookUpdate

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


@router.get("", response_model=list[Notebook])
def list_notebooks():
    return repo.list_notebooks()


@router.post("", response_model=Notebook, status_code=201)
def create_notebook(body: NotebookCreate):
    return repo.create_notebook(body.name, body.description, body.emoji)


@router.get("/{notebook_id}", response_model=Notebook)
def get_notebook(notebook_id: str):
    nb = repo.get_notebook(notebook_id)
    if not nb:
        raise HTTPException(404, "Notebook not found")
    return nb


@router.patch("/{notebook_id}", response_model=Notebook)
def update_notebook(notebook_id: str, body: NotebookUpdate):
    if not repo.get_notebook(notebook_id):
        raise HTTPException(404, "Notebook not found")
    return repo.update_notebook(
        notebook_id, name=body.name, description=body.description, emoji=body.emoji
    )


@router.delete("/{notebook_id}", status_code=204)
def delete_notebook(notebook_id: str):
    if not repo.get_notebook(notebook_id):
        raise HTTPException(404, "Notebook not found")
    repo.delete_notebook(notebook_id)
