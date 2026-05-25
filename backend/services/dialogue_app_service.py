"""Orchestration layer bridging repositories and the Phase 3 dialogue policy."""

from __future__ import annotations

from backend.repositories.external_data_repository import ExternalDataRepository
from backend.repositories.nlu_repository import NLUPredictor
from backend.repositories.session_repository import SessionRepository
from backend.schemas.dialogue import DialogueMessageResponse
from services.dialogue_manager.engine import DialogueEngine
from services.query_builder import build_nvd_query


class DialogueApplicationService:
    """Coordinates NLU interpretations, conversational memory, and scripted replies."""

    def __init__(
        self,
        nlu_repository: NLUPredictor,
        session_repository: SessionRepository,
        dialogue_engine: DialogueEngine | None = None,
        external_data_repository: ExternalDataRepository | None = None,
    ) -> None:
        self._nlu = nlu_repository
        self._sessions = session_repository
        self._engine = dialogue_engine or DialogueEngine()
        self._external_data = external_data_repository or ExternalDataRepository()

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
                reply = _format_retrieval_reply(outcome.intent, retrieval)

        self._sessions.persist(canonical_id, session)

        return DialogueMessageResponse(
            session_id=canonical_id,
            reply=reply,
            dialogue=outcome.to_dict(),
            nlu=interpretation.to_dict(),
            retrieval=retrieval,
        )


def _format_retrieval_reply(intent: str, retrieval: dict[str, object]) -> str:
    """Minimal deterministic replies until Phase 5 response generation replaces them."""

    errors = retrieval.get("errors", [])
    if isinstance(errors, list) and errors:
        return "Unable to retrieve vulnerability data from NVD at the moment."

    cves_raw = retrieval.get("cves", [])
    cves = cves_raw if isinstance(cves_raw, list) else []
    if not cves:
        return "No matching vulnerabilities were found."

    first = cves[0] if isinstance(cves[0], dict) else {}

    if intent == "CVSS_QUERY":
        cve_id = first.get("cve_id", "Unknown CVE")
        score = first.get("cvss_score", 0.0)
        severity = first.get("severity", "UNKNOWN")
        return f"{cve_id}: CVSS {score}, severity {severity}."

    if intent == "CVE_LOOKUP":
        cve_id = first.get("cve_id", "Unknown CVE")
        description = first.get("description", "")
        techniques_raw = retrieval.get("mitre_techniques", [])
        techniques = techniques_raw if isinstance(techniques_raw, list) else []
        technique_names = [
            str(item.get("name", ""))
            for item in techniques
            if isinstance(item, dict) and item.get("name")
        ]
        if technique_names:
            joined = ", ".join(technique_names[:3])
            return f"{cve_id}: {description} Related ATT&CK techniques: {joined}."
        return f"{cve_id}: {description}"

    return f"Found {len(cves)} matching vulnerabilities."
