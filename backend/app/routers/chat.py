from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import repositories as repo
from ..schemas import ChatMessage, ChatRequest
from ..services import chat as chat_service

router = APIRouter(prefix="/api/notebooks/{notebook_id}/chat", tags=["chat"])


def _require_notebook(notebook_id: str):
    if not repo.get_notebook(notebook_id):
        raise HTTPException(404, "Notebook not found")


@router.get("", response_model=list[ChatMessage])
def get_history(notebook_id: str):
    _require_notebook(notebook_id)
    return chat_service.history(notebook_id)


@router.post("", response_model=ChatMessage)
def send_message(notebook_id: str, body: ChatRequest):
    _require_notebook(notebook_id)
    return chat_service.ask(notebook_id, body.message, body.source_ids)


@router.delete("", status_code=204)
def clear_history(notebook_id: str):
    _require_notebook(notebook_id)
    chat_service.reset(notebook_id)
