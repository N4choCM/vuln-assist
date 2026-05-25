"""Deterministic mapping from NLU intents to external API queries."""

from services.query_builder.builder import build_nvd_query

__all__ = ["build_nvd_query"]
