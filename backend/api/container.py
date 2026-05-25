"""Application wiring helpers reused by lifespan hooks and tests."""

from __future__ import annotations

import os

from backend.repositories.external_data_repository import ExternalDataRepository
from backend.repositories.nlu_repository import NLURepository
from backend.repositories.session_repository import SessionRepository
from backend.services.dialogue_app_service import DialogueApplicationService
from services.dialogue_manager.engine import DialogueEngine
from services.nlu.pipeline import NLUPipeline


def build_production_dialogue_application_service() -> DialogueApplicationService:
    """Create the default Torch-backed stack used outside isolated tests."""

    model_family = os.environ.get("NLU_MODEL_FAMILY", "bert")
    pipeline = NLUPipeline(model_family=model_family)

    return DialogueApplicationService(
        nlu_repository=NLURepository(pipeline),
        session_repository=SessionRepository(),
        dialogue_engine=DialogueEngine(),
        external_data_repository=ExternalDataRepository(),
    )
