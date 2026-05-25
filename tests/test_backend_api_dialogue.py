"""HTTP smoke tests exercising controllers with mocked Torch boundaries."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.repositories.session_repository import SessionRepository
from backend.services.dialogue_app_service import DialogueApplicationService
from services.dialogue_manager import DialogueEngine
from services.nlu.models import EntityPrediction, NLUResult


def _prediction_factory() -> Callable[[str], NLUResult]:
    """Produce canned NLU output independent of heavyweight inference."""

    def _predict(_: str) -> NLUResult:
        return NLUResult(
            text="stub text",
            intent="CVE_LOOKUP",
            intent_confidence=0.9,
            entities=[
                EntityPrediction(
                    entity_type="CVE_ID",
                    value="CVE-2025-4242",
                    start=4,
                    end=18,
                    confidence=0.88,
                )
            ],
        )

    return _predict


class _StubNLUPredictor:
    """Structural equivalent of NLURepository for tests."""

    def __init__(self, predictor: Callable[[str], NLUResult]) -> None:
        self._predictor = predictor

    def predict(self, text: str) -> NLUResult:
        return self._predictor(text)


def test_dialogue_route_returns_bundle() -> None:
    predictor = _StubNLUPredictor(_prediction_factory())
    service = DialogueApplicationService(
        nlu_repository=predictor,
        session_repository=SessionRepository(),
        dialogue_engine=DialogueEngine(),
    )
    application = create_app(dialogue_application_service=service)

    with TestClient(application) as client:
        response = client.post(
            "/v1/dialogue/message",
            json={"text": "What is CVE-2025-4242?", "session_id": None},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["dialogue"]["ready_for_external_query"] is True


def test_session_ids_are_stable_across_turns() -> None:
    turns: tuple[NLUResult, NLUResult] = (
        NLUResult(
            text="first",
            intent="PRODUCT_SEARCH",
            intent_confidence=0.8,
            entities=[],
        ),
        NLUResult(
            text="Ubuntu",
            intent="PRODUCT_SEARCH",
            intent_confidence=0.8,
            entities=[
                EntityPrediction("PRODUCT", "Ubuntu", 0, 6, confidence=0.85),
            ],
        ),
    )

    class _SequencePredictor:
        """Expose stacked NLU payloads for multi-turn regressions."""

        def __init__(self, sequence: tuple[NLUResult, NLUResult]) -> None:
            self._sequence = sequence
            self._index = 0

        def predict(self, text: str) -> NLUResult:
            if self._index >= len(self._sequence):
                raise AssertionError("No additional stacked predictions configured")
            result = self._sequence[self._index]
            self._index += 1
            return result

    predictor = _SequencePredictor(turns)
    service = DialogueApplicationService(
        nlu_repository=predictor,
        session_repository=SessionRepository(),
        dialogue_engine=DialogueEngine(),
    )
    application = create_app(dialogue_application_service=service)

    with TestClient(application) as client:
        first = client.post("/v1/dialogue/message", json={"text": "find product"})
        assert first.status_code == 200
        session_payload = first.json()["session_id"]

        second = client.post(
            "/v1/dialogue/message",
            json={"session_id": session_payload, "text": "Ubuntu"},
        )
        assert second.status_code == 200
        payload = second.json()
        assert payload["session_id"] == session_payload
        assert payload["dialogue"]["intent"] == "PRODUCT_SEARCH"


def test_health_reports_models_directories() -> None:
    predictor = _StubNLUPredictor(_prediction_factory())
    application = create_app(
        dialogue_application_service=DialogueApplicationService(
            nlu_repository=predictor,
            session_repository=SessionRepository(),
            dialogue_engine=DialogueEngine(),
        )
    )
    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert "models_ready" in payload
    assert isinstance(payload["models_ready"], bool)
