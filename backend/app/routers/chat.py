from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .. import repositories as repo
from ..schemas import ChatMessage, ChatRequest
from ..services import chat as chat_service
from ..services import studio as studio_service

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


@router.post("/stream")
def send_message_stream(notebook_id: str, body: ChatRequest):
    _require_notebook(notebook_id)

    def event_stream():
        for event in chat_service.ask_stream(notebook_id, body.message, body.source_ids):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("", status_code=204)
def clear_history(notebook_id: str):
    _require_notebook(notebook_id)
    chat_service.reset(notebook_id)


@router.get("/suggestions", response_model=list[str])
def suggestions(notebook_id: str):
    _require_notebook(notebook_id)
    return studio_service.suggested_questions(notebook_id)
