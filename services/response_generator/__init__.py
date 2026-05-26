"""Phase 5 grounded response generation from structured retrieval data."""

from services.response_generator.fallback import format_retrieval_reply
from services.response_generator.generator import ResponseGenerator

__all__ = ["ResponseGenerator", "format_retrieval_reply"]
