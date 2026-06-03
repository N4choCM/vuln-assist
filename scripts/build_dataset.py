#!/usr/bin/env python3
"""Dataset generation pipeline."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Allow the script to be executed directly without installing the project as a package.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.dataset.pipeline import DatasetBuilder, DatasetSplitter, DatasetValidator, DatasetWriter
from data.dataset.settings import DEFAULT_SAMPLE_COUNT, MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT
from data.knowledge_base import KnowledgeBaseRepository, NVDRecordNormalizer, NormalizedCVE
from integrations.nvd import NVDClient, NVDClientConfig, NVDQuery


@dataclass
class PipelineTiming:
    """Collect per-phase wall times when ``--log-timing`` is enabled."""

    phases: dict[str, float] = field(default_factory=dict)
    nvd_metadata: dict[str, object] = field(default_factory=dict)

    class _Phase:
        def __init__(self, timing: "PipelineTiming", name: str) -> None:
            self._timing = timing
            self._name = name
            self._started_at = 0.0

        def __enter__(self) -> "PipelineTiming._Phase":
            self._started_at = time.monotonic()
            return self

        def __exit__(self, *_args: object) -> None:
            self._timing.phases[self._name] = time.monotonic() - self._started_at

    def phase(self, name: str) -> _Phase:
        return self._Phase(self, name)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    timing = PipelineTiming() if args.log_timing else None
    pipeline_started_at = time.monotonic()

    print("Dataset generation pipeline")
    print(f"- project root: {PROJECT_ROOT}")
    print(f"- requested samples: {args.samples}")
    if args.log_timing:
        print("- timing log: enabled")

    # Load the active KB before touching dataset-specific generation logic.
    if timing is not None:
        with timing.phase("knowledge_base"):
            records = load_knowledge_base(args, timing)
    else:
        records = load_knowledge_base(args, timing)
    print(f"- knowledge base records available: {len(records)}")

    # Build samples from templates, real entities, paraphrases, and BIO annotations.
    print("Generating template-based samples with real entity injection...")
    if timing is not None:
        with timing.phase("sample_generation"):
            samples = _build_samples(records, args.samples, args.seed)
    else:
        samples = _build_samples(records, args.samples, args.seed)
    print(f"- generated samples: {len(samples)}")

    # Keep model-training splits reproducible and close to the required 70/15/15 ratio.
    print("Creating 70/15/15 train, validation, and test splits...")
    if timing is not None:
        with timing.phase("split"):
            splits = _split_samples(samples, args.seed)
    else:
        splits = _split_samples(samples, args.seed)
    for split_name, split_samples in splits.items():
        print(f"- {split_name}: {len(split_samples)} samples")

    # Validate before writing so broken datasets never overwrite the target output.
    print("Validating intent coverage, entity spans, BIO tags, and split ratios...")
    if timing is not None:
        with timing.phase("validation"):
            _validate_splits(splits)
    else:
        _validate_splits(splits)

    print(f"Writing outputs to {args.output_dir}...")
    if timing is not None:
        with timing.phase("write"):
            writer = _write_outputs(args.output_dir, splits)
    else:
        writer = _write_outputs(args.output_dir, splits)
    print(f"- intents: {writer.intents_path}")
    print(f"- NER CoNLL: {writer.ner_path}")

    if timing is not None:
        timing.phases["total"] = time.monotonic() - pipeline_started_at
        _print_timing_summary(timing, args)

    print("Dataset pipeline completed successfully.")
    return 0


def _build_samples(records: list[NormalizedCVE], sample_count: int, seed: int) -> list:
    builder = DatasetBuilder(records=records, sample_count=sample_count, seed=seed)
    return builder.build()


def _split_samples(samples: list, seed: int) -> dict[str, list]:
    return DatasetSplitter(seed=seed).split(samples)


def _validate_splits(splits: dict[str, list]) -> None:
    validator = DatasetValidator()
    report = validator.validate(splits)
    for warning in report.warnings:
        print(f"- warning: {warning}")
    validator.raise_for_errors(report)


def _write_outputs(output_dir: Path, splits: dict[str, list]) -> DatasetWriter:
    writer = DatasetWriter(output_dir)
    writer.write(splits)
    return writer


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the NLU dataset.")
    parser.add_argument(
        "--samples",
        type=int,
        default=DEFAULT_SAMPLE_COUNT,
        help=f"Total samples, from {MIN_SAMPLE_COUNT} to {MAX_SAMPLE_COUNT}.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Deterministic generation seed.")
    # Path arguments accept both absolute paths and project-relative paths.
    parser.add_argument(
        "--kb-path",
        type=resolve_project_path,
        default=PROJECT_ROOT / "data" / "knowledge_base" / "cves.json",
        help="Path to the normalized CVE knowledge base JSON.",
    )
    parser.add_argument(
        "--seed-kb-path",
        type=resolve_project_path,
        default=PROJECT_ROOT / "data" / "knowledge_base" / "seed_cves.json",
        help="Controlled NVD-derived fallback knowledge base.",
    )
    parser.add_argument(
        "--output-dir",
        type=resolve_project_path,
        default=PROJECT_ROOT / "data" / "dataset" / "output",
        help="Directory for intents.json and ner.conll.",
    )
    parser.add_argument(
        "--refresh-nvd",
        action="store_true",
        help="Fetch CVEs from NVD before building the dataset.",
    )
    parser.add_argument(
        "--nvd-limit",
        type=int,
        default=100,
        help="Maximum number of raw NVD records to fetch when --refresh-nvd is set.",
    )
    parser.add_argument(
        "--nvd-keyword",
        default=None,
        help="Optional NVD keywordSearch value used with --refresh-nvd.",
    )
    parser.add_argument(
        "--log-timing",
        action="store_true",
        help=(
            "Print per-phase wall times and NVD client settings "
            "(use to compare runs with and without NVD_API_KEY)."
        ),
    )
    return parser.parse_args(argv)


def resolve_project_path(value: str) -> Path:
    """Resolve CLI paths relative to the project root when they are not absolute."""

    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_knowledge_base(
    args: argparse.Namespace,
    timing: Optional[PipelineTiming] = None,
) -> list[NormalizedCVE]:
    repository = KnowledgeBaseRepository(args.kb_path)

    # Optional live refresh keeps external access explicit and preserves local reproducibility.
    if args.refresh_nvd:
        refreshed = refresh_from_nvd(args, timing)
        if refreshed:
            repository.save(refreshed)
            print(f"- refreshed normalized KB from NVD: {repository.path}")
            return refreshed
        print("- NVD refresh did not produce usable records; falling back to local KB.")

    if repository.exists():
        print(f"Loading normalized KB from {repository.path}...")
        return repository.load()

    # First-run fallback: seed data is already normalized and NVD-derived.
    print(f"Normalized KB not found at {repository.path}.")
    print(f"Loading controlled NVD-derived seed KB from {args.seed_kb_path}...")
    seed_repository = KnowledgeBaseRepository(args.seed_kb_path)
    records = seed_repository.load()
    repository.save(records)
    print(f"- initialized normalized KB at {repository.path}")
    return records


def refresh_from_nvd(
    args: argparse.Namespace,
    timing: Optional[PipelineTiming] = None,
) -> list[NormalizedCVE]:
    print("Fetching CVE records from NVD...")
    client_config = NVDClientConfig.from_environment()
    query = NVDQuery(keyword_search=args.nvd_keyword) if args.nvd_keyword else None

    fetch_started_at = time.monotonic()
    try:
        raw_records = NVDClient(client_config).fetch_cves(query=query, total_limit=args.nvd_limit)
    except Exception as exc:
        print(f"- NVD fetch failed: {exc}")
        return []
    nvd_fetch_seconds = time.monotonic() - fetch_started_at

    print(f"- raw NVD records fetched: {len(raw_records)}")
    if timing is not None:
        timing.phases["nvd_fetch"] = nvd_fetch_seconds
        timing.nvd_metadata = {
            "api_key_configured": client_config.api_key is not None,
            "request_interval_seconds": client_config.effective_request_interval,
            "nvd_limit": args.nvd_limit,
            "raw_records_fetched": len(raw_records),
        }

    normalizer = NVDRecordNormalizer()
    normalize_started_at = time.monotonic()
    normalized = normalizer.normalize_many(raw_records)
    if timing is not None:
        timing.phases["nvd_normalize"] = time.monotonic() - normalize_started_at

    # Dataset generation needs concrete entities, so prefer records with product/version data.
    usable = [record for record in normalized if record.products and record.versions]
    print(f"- normalized records: {len(normalized)}")
    print(f"- records with products and versions: {len(usable)}")
    if timing is not None:
        timing.nvd_metadata["normalized_records"] = len(normalized)
        timing.nvd_metadata["usable_records"] = len(usable)
    return usable or normalized


def _print_timing_summary(timing: PipelineTiming, args: argparse.Namespace) -> None:
    """Emit a compact timing report suitable for thesis benchmarks."""

    print("Timing summary")
    phase_order = (
        "nvd_fetch",
        "nvd_normalize",
        "knowledge_base",
        "sample_generation",
        "split",
        "validation",
        "write",
        "total",
    )
    for phase_name in phase_order:
        if phase_name in timing.phases:
            print(f"- {phase_name}: {timing.phases[phase_name]:.2f}s")

    if timing.nvd_metadata:
        api_key = "yes" if timing.nvd_metadata.get("api_key_configured") else "no"
        interval = timing.nvd_metadata.get("request_interval_seconds")
        print(
            "- nvd_client: "
            f"api_key={api_key}, "
            f"request_interval={interval}s, "
            f"nvd_limit={timing.nvd_metadata.get('nvd_limit')}, "
            f"raw_records={timing.nvd_metadata.get('raw_records_fetched')}"
        )
    elif args.refresh_nvd:
        print("- nvd_client: refresh requested but no NVD timing was recorded")


if __name__ == "__main__":
    raise SystemExit(main())
