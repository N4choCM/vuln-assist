"""Shared dataset generation settings."""

from __future__ import annotations


# Keep sample-count policy centralized so CLI help, generation, and validation agree.
MIN_SAMPLE_COUNT = 100
MAX_SAMPLE_COUNT = 1000
DEFAULT_SAMPLE_COUNT = 120
