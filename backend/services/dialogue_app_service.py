"""Orchestration layer bridging repositories and the Phase 3 dialogue policy."""

from __future__ import annotations

from backend.repositories.nlu_repository import NLUPredictor
from backend.repositories.session_repository import SessionRepository
from backend.schemas.dialogue import DialogueMessageResponse
from services.dialogue_manager.engine import DialogueEngine


class DialogueApplicationService:
    """Coordinates NLU interpretations, conversational memory, and scripted replies."""

    def __init__(
        self,
        nlu_repository: NLUPredictor,
        session_repository: SessionRepository,
        dialogue_engine: DialogueEngine | None = None,
    ) -> None:
        self._nlu = nlu_repository
        self._sessions = session_repository
        self._engine = dialogue_engine or DialogueEngine()

    def exchange(self, *, session_id: str | None, text: str) -> DialogueMessageResponse:
        normalized = text.strip()
        canonical_id, session = self._sessions.get_or_create(session_id)
        interpretation = self._nlu.predict(normalized)
        outcome = self._engine.process_turn(session, interpretation)

        self._sessions.persist(canonical_id, session)

        return DialogueMessageResponse(
            session_id=canonical_id,
            reply=outcome.reply,
            dialogue=outcome.to_dict(),
            nlu=interpretation.to_dict(),
        )
