"""Session persistence backends for conversational context."""

from __future__ import annotations

from threading import Lock
from uuid import uuid4

from services.dialogue_manager.models import DialogueSession


class SessionRepository:
    """Thread-safe RAM store suited for demos and pytest fixtures."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, DialogueSession] = {}

    def get_or_create(self, session_id: str | None) -> tuple[str, DialogueSession]:
        """Return canonical id plus hydrated session."""

        resolved_id = session_id or str(uuid4())
        with self._lock:
            session = self._sessions.get(resolved_id)
            if session is None:
                session = DialogueSession()
                self._sessions[resolved_id] = session
            return resolved_id, session

    def persist(self, session_id: str, session: DialogueSession) -> None:
        """Upsert conversational memory after each orchestrated step."""

        with self._lock:
            self._sessions[session_id] = session
