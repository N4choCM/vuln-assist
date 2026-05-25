# Dialogue Manager (`services/dialogue_manager`)

Core finite-state dialogue policy that consumes [`NLUResult`](../nlu/models.py) objects and emits templated replies plus structured outcomes for later query building.

## Responsibilities

- Merge BIO-extracted spans into conversational slot memory.
- Decide when mandatory slots ([`.cursor/rules/domain.mdc`](../../.cursor/rules/domain.mdc)) are missing and ask focused clarifying questions.
- Flag when downstream CVE retrieval can start (`ready_for_external_query`) once Phase 4 integrations land.

This package **never** exposes HTTP endpoints, persists storage, touches Hugging Face models directly, nor calls external APIs—those boundaries live in [`backend/`](../../backend/README.md) and [`integrations/`](../../integrations/).

## Files

| File | Role |
|------|------|
| `models.py` | `DialogueSession` (mutable persisted state), `DialogueOutcome` payloads. |
| `engine.py` | `DialogueEngine.process_turn(...)` encapsulates the deterministic FSM transitions. |

## Usage

```python
from services.dialogue_manager import DialogueEngine, DialogueSession
from services.nlu import NLUPipeline

pipeline = NLUPipeline(model_family="bert")
engine = DialogueEngine()
session = DialogueSession()
interpretation = pipeline.predict("What is CVE-2025-1234?")

outcome = engine.process_turn(session, interpretation)
print(outcome.reply, outcome.ready_for_external_query)
```

## Extension hooks

Phase 4 injects repositories that hydrate cache lines from `integrations/`; this module intentionally stops at deterministic responses with `blocked_reason="integrations_pending"` when external data is unavailable.
