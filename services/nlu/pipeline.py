"""Runtime NLU prediction pipeline."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from services.nlu.config import DEFAULT_CONFIG_PATH, DEFAULT_MODELS_DIR, load_training_config
from services.nlu.models import EntityPrediction, NLUResult


# Mirror the Phase 1 BIO token boundaries so runtime NER sees the same word units as training.
_TOKEN_PATTERN = re.compile(
    r"CVE-\d{4}-\d{4,7}|[A-Za-z0-9]+(?:[._/-][A-Za-z0-9]+)*|[^\w\s]",
    re.IGNORECASE,
)


class NLUPipeline:
    """Load trained intent and NER models for one model family."""

    def __init__(
        self,
        model_family: str = "bert",
        models_dir: Path = DEFAULT_MODELS_DIR,
        config_path: Path = DEFAULT_CONFIG_PATH,
    ) -> None:
        self._model_family = model_family
        self._models_dir = models_dir
        self._config = load_training_config(config_path)
        self._intent_tokenizer: Any = None
        self._intent_model: Any = None
        self._ner_tokenizer: Any = None
        self._ner_model: Any = None

    def predict(self, text: str) -> NLUResult:
        """Return the structured NLU interpretation of one user query."""

        self._load_once()
        intent, intent_confidence = self._predict_intent(text)
        entities = self._predict_entities(text)
        return NLUResult(
            text=text,
            intent=intent,
            intent_confidence=intent_confidence,
            entities=entities,
        )

    def _load_once(self) -> None:
        if self._intent_model is not None and self._ner_model is not None:
            return

        from transformers import AutoModelForSequenceClassification
        from transformers import AutoModelForTokenClassification
        from transformers import AutoTokenizer

        base_dir = self._models_dir / self._model_family
        intent_dir = base_dir / "intent"
        ner_dir = base_dir / "ner"
        if not intent_dir.exists() or not ner_dir.exists():
            raise FileNotFoundError(
                "Trained NLU models were not found. Run "
                f"`python3 scripts/train_nlu.py --model-family {self._model_family}` first."
            )

        self._intent_tokenizer = AutoTokenizer.from_pretrained(intent_dir)
        self._intent_model = AutoModelForSequenceClassification.from_pretrained(intent_dir)
        self._ner_tokenizer = AutoTokenizer.from_pretrained(ner_dir)
        self._ner_model = AutoModelForTokenClassification.from_pretrained(ner_dir)
        self._intent_model.eval()
        self._ner_model.eval()

    def _predict_intent(self, text: str) -> tuple[str, float]:
        import torch

        inputs = self._intent_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self._config.max_length,
        )
        with torch.no_grad():
            logits = self._intent_model(**inputs).logits[0]
            probabilities = torch.softmax(logits, dim=-1)
        label_id = int(torch.argmax(probabilities).item())
        return self._label_for_id(self._intent_model.config.id2label, label_id), float(
            probabilities[label_id].item()
        )

    def _predict_entities(self, text: str) -> list[EntityPrediction]:
        import torch

        token_spans = _tokenize_for_ner(text)
        if not token_spans:
            return []

        inputs = self._ner_tokenizer(
            [token for token, _, _ in token_spans],
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=self._config.max_length,
        )
        word_ids = inputs.word_ids(batch_index=0)
        with torch.no_grad():
            logits = self._ner_model(**inputs).logits[0]
            probabilities = torch.softmax(logits, dim=-1)
        label_ids = torch.argmax(probabilities, dim=-1).tolist()
        confidences = torch.max(probabilities, dim=-1).values.tolist()
        word_label_ids, word_confidences, word_offsets = self._first_subword_predictions(
            label_ids=label_ids,
            confidences=confidences,
            word_ids=word_ids,
            token_spans=token_spans,
        )
        return self._entities_from_bio(
            text=text,
            label_ids=word_label_ids,
            confidences=word_confidences,
            offsets=word_offsets,
            id_to_label=self._ner_model.config.id2label,
        )

    @staticmethod
    def _first_subword_predictions(
        label_ids: list[int],
        confidences: list[float],
        word_ids: list[int | None],
        token_spans: list[tuple[str, int, int]],
    ) -> tuple[list[int], list[float], list[list[int]]]:
        """Project subword predictions back to the first labeled word token."""

        word_label_ids: list[int] = []
        word_confidences: list[float] = []
        word_offsets: list[list[int]] = []
        previous_word_id: int | None = None

        for label_id, confidence, word_id in zip(label_ids, confidences, word_ids):
            if word_id is None:
                previous_word_id = None
                continue
            # Training masks continuation subwords with -100, so inference ignores them too.
            if word_id == previous_word_id:
                continue
            previous_word_id = word_id
            if word_id >= len(token_spans):
                continue

            _, start, end = token_spans[word_id]
            word_label_ids.append(int(label_id))
            word_confidences.append(float(confidence))
            word_offsets.append([start, end])

        return word_label_ids, word_confidences, word_offsets

    @staticmethod
    def _entities_from_bio(
        text: str,
        label_ids: list[int],
        confidences: list[float],
        offsets: list[list[int]],
        id_to_label: dict[int | str, str],
    ) -> list[EntityPrediction]:
        entities: list[EntityPrediction] = []
        current_type = ""
        current_start = 0
        current_end = 0
        current_scores: list[float] = []

        def flush() -> None:
            nonlocal current_type, current_start, current_end, current_scores
            if not current_type:
                return
            start, end = _trim_span(text, current_start, current_end)
            if start < end:
                entities.append(
                    EntityPrediction(
                        entity_type=current_type,
                        value=text[start:end],
                        start=start,
                        end=end,
                        confidence=sum(current_scores) / len(current_scores),
                    )
                )
            current_type = ""
            current_start = 0
            current_end = 0
            current_scores = []

        for label_id, confidence, offset in zip(label_ids, confidences, offsets):
            start, end = int(offset[0]), int(offset[1])
            if start == end:
                continue

            label = NLUPipeline._label_for_id(id_to_label, int(label_id))
            if label == "O":
                flush()
                continue

            prefix, entity_type = label.split("-", maxsplit=1)
            if prefix == "B" or entity_type != current_type:
                flush()
                current_type = entity_type
                current_start = start
                current_end = end
                current_scores = [float(confidence)]
                continue

            # Valid I-tags extend the active entity span.
            current_end = end
            current_scores.append(float(confidence))

        flush()
        return entities

    @staticmethod
    def _label_for_id(id_to_label: dict[int | str, str], label_id: int) -> str:
        return id_to_label.get(label_id) or id_to_label[str(label_id)]


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _tokenize_for_ner(text: str) -> list[tuple[str, int, int]]:
    """Return runtime NER tokens with character spans preserved."""

    return [
        (match.group(0), match.start(), match.end())
        for match in _TOKEN_PATTERN.finditer(text)
    ]
