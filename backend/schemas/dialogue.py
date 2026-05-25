"""Pydantic models for HTTP payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DialogueMessageRequest(BaseModel):
    """Inbound user utterance routed through NLU."""

    session_id: str | None = Field(default=None, max_length=256)
    text: str = Field(..., min_length=1)


class DialogueMessageResponse(BaseModel):
    """Echoes interpretations plus scripted assistant replies."""

    session_id: str
    reply: str
    dialogue: dict[str, object]
    nlu: dict[str, object]
