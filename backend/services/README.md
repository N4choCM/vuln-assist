# Backend Application Services (`backend/services/`)

Use-case classes consumed by controllers. **`DialogueApplicationService`** stitches together repositories and the deterministic [`services.dialogue_manager.DialogueEngine`](../../services/dialogue_manager/README.md):

1. Recover or mint a conversational session identifier.
2. Run NLU through `NLUPredictor` (usually `backend.repositories.NLURepository`).
3. Feed results into `DialogueEngine.process_turn(...)`.
4. When slots are complete, fetch NVD/MITRE data and generate a grounded reply via `ResponseGeneratorRepository`.
5. Persist updated slot memory inside `SessionRepository`.
6. Return Pydantic response objects destined for routers.
