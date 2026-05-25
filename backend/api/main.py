"""FastAPI entrypoint reserved for lifespan wiring plus router mounting."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.container import build_production_dialogue_application_service
from backend.controllers.dialogue import router as dialogue_router
from backend.controllers.health import router as health_router
from backend.services.dialogue_app_service import DialogueApplicationService


@asynccontextmanager
async def _production_lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.dialogue_application_service = build_production_dialogue_application_service()
    yield


def create_app(*, dialogue_application_service: DialogueApplicationService | None = None) -> FastAPI:
    """Factory enabling lightweight dependency injection inside pytest suites."""

    if dialogue_application_service is None:
        lifespan = _production_lifespan
        app = FastAPI(
            lifespan=lifespan,
            title="Cybersecurity Dialogue API",
            version="0.1.0",
        )
    else:
        @asynccontextmanager
        async def _fixture_lifetime(app_fixture: FastAPI) -> AsyncIterator[None]:
            app_fixture.state.dialogue_application_service = dialogue_application_service
            yield

        app = FastAPI(
            lifespan=_fixture_lifetime,
            title="Cybersecurity Dialogue API",
            version="0.1.0",
        )

    app.include_router(health_router)
    app.include_router(dialogue_router)
    return app


app = create_app()
