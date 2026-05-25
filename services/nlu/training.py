"""Training orchestration for Phase 2 NLU models."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

from services.nlu.config import (
    DEFAULT_DATASET_DIR,
    DEFAULT_MODELS_DIR,
    NLUTrainingConfig,
)
from services.nlu.datasets import (
    build_intent_dataset,
    build_ner_dataset,
    load_intent_splits,
    load_ner_splits,
)
from services.nlu.labels import (
    BIO_ID_TO_LABEL,
    BIO_LABEL_TO_ID,
    INTENT_ID_TO_LABEL,
    INTENT_LABEL_TO_ID,
)
from services.nlu.metrics import compute_classification_metrics, compute_ner_metrics


def train_all(
    config: NLUTrainingConfig,
    intents_path: Path = DEFAULT_DATASET_DIR / "intents.json",
    ner_path: Path = DEFAULT_DATASET_DIR / "ner.conll",
    output_dir: Path = DEFAULT_MODELS_DIR,
) -> dict[str, dict[str, Any]]:
    """Train and evaluate every configured model family."""

    summary: dict[str, dict[str, Any]] = {}
    for model_family in config.models:
        summary[model_family] = train_model_family(
            model_family=model_family,
            config=config,
            intents_path=intents_path,
            ner_path=ner_path,
            output_dir=output_dir,
        )
    _write_json(output_dir / "evaluation_summary.json", summary)
    return summary


def train_model_family(
    model_family: str,
    config: NLUTrainingConfig,
    intents_path: Path = DEFAULT_DATASET_DIR / "intents.json",
    ner_path: Path = DEFAULT_DATASET_DIR / "ner.conll",
    output_dir: Path = DEFAULT_MODELS_DIR,
) -> dict[str, Any]:
    """Train intent and NER heads for one HuggingFace model family."""

    pretrained_name = config.model_name(model_family)
    base_output_dir = output_dir / model_family
    base_output_dir.mkdir(parents=True, exist_ok=True)

    intent_metrics = _train_intent_model(
        pretrained_name=pretrained_name,
        config=config,
        intents_path=intents_path,
        output_dir=base_output_dir / "intent",
    )
    ner_metrics = _train_ner_model(
        pretrained_name=pretrained_name,
        config=config,
        ner_path=ner_path,
        output_dir=base_output_dir / "ner",
    )
    metrics = {
        "model_family": model_family,
        "pretrained_model_name": pretrained_name,
        "intent": intent_metrics,
        "ner": ner_metrics,
    }
    _write_json(base_output_dir / "metrics.json", metrics)
    return metrics


def _train_intent_model(
    pretrained_name: str,
    config: NLUTrainingConfig,
    intents_path: Path,
    output_dir: Path,
) -> dict[str, float]:
    from transformers import AutoModelForSequenceClassification, Trainer

    tokenizer = _load_tokenizer(pretrained_name)
    splits = load_intent_splits(intents_path)
    train_dataset = build_intent_dataset(
        splits["train"], tokenizer, INTENT_LABEL_TO_ID, config.max_length
    )
    validation_dataset = build_intent_dataset(
        splits["validation"], tokenizer, INTENT_LABEL_TO_ID, config.max_length
    )
    test_dataset = build_intent_dataset(
        splits["test"], tokenizer, INTENT_LABEL_TO_ID, config.max_length
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        pretrained_name,
        num_labels=len(INTENT_LABEL_TO_ID),
        id2label=INTENT_ID_TO_LABEL,
        label2id=INTENT_LABEL_TO_ID,
    )
    trainer = Trainer(
        model=model,
        args=_training_arguments(output_dir, config),
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        compute_metrics=compute_classification_metrics,
        callbacks=_early_stopping_callbacks(config),
    )
    trainer.train()
    metrics = _clean_metrics(trainer.evaluate(test_dataset))
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    return metrics


def _train_ner_model(
    pretrained_name: str,
    config: NLUTrainingConfig,
    ner_path: Path,
    output_dir: Path,
) -> dict[str, float]:
    from transformers import AutoModelForTokenClassification, Trainer

    tokenizer = _load_tokenizer(pretrained_name, pretokenized=True)
    splits = load_ner_splits(ner_path)
    train_dataset = build_ner_dataset(
        splits["train"], tokenizer, BIO_LABEL_TO_ID, config.max_length
    )
    validation_dataset = build_ner_dataset(
        splits["validation"], tokenizer, BIO_LABEL_TO_ID, config.max_length
    )
    test_dataset = build_ner_dataset(
        splits["test"], tokenizer, BIO_LABEL_TO_ID, config.max_length
    )
    model = AutoModelForTokenClassification.from_pretrained(
        pretrained_name,
        num_labels=len(BIO_LABEL_TO_ID),
        id2label=BIO_ID_TO_LABEL,
        label2id=BIO_LABEL_TO_ID,
    )
    trainer = Trainer(
        model=model,
        args=_training_arguments(output_dir, config),
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        compute_metrics=lambda eval_pred: compute_ner_metrics(eval_pred, BIO_ID_TO_LABEL),
        callbacks=_early_stopping_callbacks(config),
    )
    trainer.train()
    metrics = _clean_metrics(trainer.evaluate(test_dataset))
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    return metrics


def _training_arguments(output_dir: Path, config: NLUTrainingConfig) -> Any:
    from transformers import TrainingArguments

    kwargs: dict[str, Any] = {
        "output_dir": str(output_dir),
        "learning_rate": config.learning_rate,
        "per_device_train_batch_size": config.batch_size,
        "per_device_eval_batch_size": config.batch_size,
        "num_train_epochs": config.num_train_epochs,
        "weight_decay": 0.01,
        "logging_strategy": "epoch",
        "save_strategy": "epoch",
        "load_best_model_at_end": True,
        "metric_for_best_model": "f1",
        "greater_is_better": True,
        "save_total_limit": 1,
        "report_to": [],
        "seed": config.seed,
    }
    # Transformers renamed this argument; inspect keeps the code version-tolerant.
    parameters = inspect.signature(TrainingArguments.__init__).parameters
    if "eval_strategy" in parameters:
        kwargs["eval_strategy"] = "epoch"
    else:
        kwargs["evaluation_strategy"] = "epoch"
    return TrainingArguments(**kwargs)


def _load_tokenizer(pretrained_name: str, pretokenized: bool = False) -> Any:
    from transformers import AutoTokenizer

    kwargs: dict[str, Any] = {"use_fast": True}
    if pretokenized and "roberta" in pretrained_name.lower():
        # RoBERTa fast tokenizers require this flag for is_split_into_words inputs.
        kwargs["add_prefix_space"] = True
    return AutoTokenizer.from_pretrained(pretrained_name, **kwargs)


def _early_stopping_callbacks(config: NLUTrainingConfig) -> list[Any]:
    from transformers import EarlyStoppingCallback

    return [
        EarlyStoppingCallback(
            early_stopping_patience=config.early_stopping_patience,
        )
    ]


def _clean_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    clean: dict[str, float] = {}
    for key, value in metrics.items():
        if not key.startswith("eval_"):
            continue
        normalized_key = key.removeprefix("eval_")
        if normalized_key in {"accuracy", "precision", "recall", "f1", "loss"}:
            clean[normalized_key] = float(value)
    return clean


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")
