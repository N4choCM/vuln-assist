"""Orchestration layer bridging repositories and the Phase 3 dialogue policy."""

from __future__ import annotations

from backend.repositories.external_data_repository import ExternalDataRepository
from backend.repositories.nlu_repository import NLUPredictor
from backend.repositories.response_generator_repository import ResponseGeneratorRepository
from backend.repositories.session_repository import SessionRepository
from backend.schemas.dialogue import DialogueMessageResponse
from services.dialogue_manager.engine import DialogueEngine
from services.query_builder import build_nvd_query
from services.response_generator.generator import ResponseGenerator


class DialogueApplicationService:
    """Coordinates NLU interpretations, conversational memory, and scripted replies."""

    def __init__(
        self,
        nlu_repository: NLUPredictor,
        session_repository: SessionRepository,
        dialogue_engine: DialogueEngine | None = None,
        external_data_repository: ExternalDataRepository | None = None,
        response_generator_repository: ResponseGeneratorRepository | None = None,
    ) -> None:
        self._nlu = nlu_repository
        self._sessions = session_repository
        self._engine = dialogue_engine or DialogueEngine()
        self._external_data = external_data_repository or ExternalDataRepository()
        self._response_generator = response_generator_repository or ResponseGeneratorRepository(
            ResponseGenerator()
        )

    def exchange(self, *, session_id: str | None, text: str) -> DialogueMessageResponse:
        normalized = text.strip()
        canonical_id, session = self._sessions.get_or_create(session_id)
        interpretation = self._nlu.predict(normalized)
        outcome = self._engine.process_turn(session, interpretation)

        retrieval: dict[str, object] | None = None
        reply = outcome.reply
        if outcome.ready_for_external_query:
            built = build_nvd_query(outcome.intent, outcome.slots)
            if built is not None:
                query, limit = built
                retrieval = self._external_data.fetch(outcome.intent, outcome.slots, query, limit)
                reply = self._response_generator.generate(normalized, outcome.intent, retrieval)

        self._sessions.persist(canonical_id, session)

        return DialogueMessageResponse(
            session_id=canonical_id,
            reply=reply,
            dialogue=outcome.to_dict(),
            nlu=interpretation.to_dict(),
            retrieval=retrieval,
        )
