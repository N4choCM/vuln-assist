#!/usr/bin/env python3
"""Dataset generation pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Allow the script to be executed directly without installing the project as a package.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.dataset.pipeline import DatasetBuilder, DatasetSplitter, DatasetValidator, DatasetWriter
from data.dataset.settings import DEFAULT_SAMPLE_COUNT, MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT
from data.knowledge_base import KnowledgeBaseRepository, NVDRecordNormalizer, NormalizedCVE
from integrations.nvd import NVDClient, NVDQuery


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    print("Dataset generation pipeline")
    print(f"- project root: {PROJECT_ROOT}")
    print(f"- requested samples: {args.samples}")

    # Load the active KB before touching dataset-specific generation logic.
    records = load_knowledge_base(args)
    print(f"- knowledge base records available: {len(records)}")

    # Build samples from templates, real entities, paraphrases, and BIO annotations.
    print("Generating template-based samples with real entity injection...")
    builder = DatasetBuilder(records=records, sample_count=args.samples, seed=args.seed)
    samples = builder.build()
    print(f"- generated samples: {len(samples)}")

    # Keep model-training splits reproducible and close to the required 70/15/15 ratio.
    print("Creating 70/15/15 train, validation, and test splits...")
    splitter = DatasetSplitter(seed=args.seed)
    splits = splitter.split(samples)
    for split_name, split_samples in splits.items():
        print(f"- {split_name}: {len(split_samples)} samples")

    # Validate before writing so broken datasets never overwrite the target output.
    print("Validating intent coverage, entity spans, BIO tags, and split ratios...")
    validator = DatasetValidator()
    report = validator.validate(splits)
    for warning in report.warnings:
        print(f"- warning: {warning}")
    validator.raise_for_errors(report)

    print(f"Writing outputs to {args.output_dir}...")
    writer = DatasetWriter(args.output_dir)
    writer.write(splits)
    print(f"- intents: {writer.intents_path}")
    print(f"- NER CoNLL: {writer.ner_path}")
    print("Dataset pipeline completed successfully.")
    return 0


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
    return parser.parse_args(argv)


def resolve_project_path(value: str) -> Path:
    """Resolve CLI paths relative to the project root when they are not absolute."""

    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_knowledge_base(args: argparse.Namespace) -> list[NormalizedCVE]:
    repository = KnowledgeBaseRepository(args.kb_path)

    # Optional live refresh keeps external access explicit and preserves local reproducibility.
    if args.refresh_nvd:
        refreshed = refresh_from_nvd(args)
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


def refresh_from_nvd(args: argparse.Namespace) -> list[NormalizedCVE]:
    print("Fetching CVE records from NVD...")
    query = NVDQuery(keyword_search=args.nvd_keyword) if args.nvd_keyword else None
    try:
        raw_records = NVDClient().fetch_cves(query=query, total_limit=args.nvd_limit)
    except Exception as exc:
        print(f"- NVD fetch failed: {exc}")
        return []

    print(f"- raw NVD records fetched: {len(raw_records)}")
    normalizer = NVDRecordNormalizer()
    normalized = normalizer.normalize_many(raw_records)
    # Dataset generation needs concrete entities, so prefer records with product/version data.
    usable = [record for record in normalized if record.products and record.versions]
    print(f"- normalized records: {len(normalized)}")
    print(f"- records with products and versions: {len(usable)}")
    return usable or normalized


if __name__ == "__main__":
    raise SystemExit(main())
