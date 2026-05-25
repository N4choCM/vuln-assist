# Backend Schemas (`backend/schemas/`)

Pydantic models describing HTTP payloads. They mirror (but deliberately stay slimmer than) internal dataclasses such as [`NLUResult`](../../services/nlu/models.py) or [`DialogueOutcome`](../../services/dialogue_manager/models.py) dictionaries returned downstream.
