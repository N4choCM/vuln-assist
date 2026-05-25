"""Expose orchestrated conversational turns rooted in layered services."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.schemas.dialogue import DialogueMessageRequest, DialogueMessageResponse
from backend.services.dialogue_app_service import DialogueApplicationService


def get_dialogue_application_service(request: Request) -> DialogueApplicationService:
    """Inject the lifespan-provisioned service without importing Torch in routers."""

    return request.app.state.dialogue_application_service


DialogueSvc = Annotated[DialogueApplicationService, Depends(get_dialogue_application_service)]

router = APIRouter(prefix="/v1/dialogue", tags=["dialogue"])


@router.post("/message")
def append_message(
    payload: DialogueMessageRequest,
    svc: DialogueSvc,
) -> DialogueMessageResponse:
    """Interpret one user statement and return scripted guidance."""

    return svc.exchange(session_id=payload.session_id, text=payload.text)
