"""Knowledge-base normalization and persistence for Phase 1."""

from data.knowledge_base.models import NormalizedCVE
from data.knowledge_base.normalizer import NVDRecordNormalizer
from data.knowledge_base.repository import KnowledgeBaseRepository

__all__ = ["KnowledgeBaseRepository", "NVDRecordNormalizer", "NormalizedCVE"]

