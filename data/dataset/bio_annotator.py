"""BIO annotation for generated cybersecurity queries."""

from __future__ import annotations

import re
from typing import Iterable

from data.dataset.models import BIOAnnotation, EntitySpan, EntityValue, TokenAnnotation


# Tokenize CVE IDs, version-like words, and punctuation without losing character offsets.
_TOKEN_PATTERN = re.compile(
    r"CVE-\d{4}-\d{4,7}|[A-Za-z0-9]+(?:[._/-][A-Za-z0-9]+)*|[^\w\s]",
    re.IGNORECASE,
)


class BIOAnnotator:
    """Tokenize query text and assign BIO tags for entity spans."""

    def annotate(self, text: str, entities: Iterable[EntityValue]) -> BIOAnnotation:
        # Locate spans before tokenization so BIO tags can be assigned by offsets.
        entity_spans = self._locate_entities(text, entities)
        tokens = self._tokenize(text)
        annotated_tokens = [self._tag_token(token, entity_spans) for token in tokens]
        return BIOAnnotation(tokens=annotated_tokens, entities=entity_spans)

    def _locate_entities(self, text: str, entities: Iterable[EntityValue]) -> list[EntitySpan]:
        spans: list[EntitySpan] = []
        occupied: list[tuple[int, int]] = []
        # Longest-first matching prevents "Apache" from stealing "Apache Log4j".
        entity_values = sorted(entities, key=lambda entity: len(entity.value), reverse=True)

        for entity in entity_values:
            if not entity.value:
                continue
            # Lookarounds require entity boundaries without consuming surrounding text.
            pattern = re.compile(r"(?<!\w)" + re.escape(entity.value) + r"(?!\w)", re.IGNORECASE)
            for match in pattern.finditer(text):
                start, end = match.span()
                # Avoid assigning overlapping spans when entity values are nested.
                if self._overlaps(start, end, occupied):
                    continue
                spans.append(
                    EntitySpan(
                        entity_type=entity.entity_type,
                        value=text[start:end],
                        start=start,
                        end=end,
                    )
                )
                occupied.append((start, end))

        return sorted(spans, key=lambda span: (span.start, span.end))

    def _tokenize(self, text: str) -> list[TokenAnnotation]:
        # Tokens start as outside entities; _tag_token upgrades them to B-/I- tags.
        return [
            TokenAnnotation(token=match.group(0), tag="O", start=match.start(), end=match.end())
            for match in _TOKEN_PATTERN.finditer(text)
        ]

    def _tag_token(self, token: TokenAnnotation, entity_spans: list[EntitySpan]) -> TokenAnnotation:
        for span in entity_spans:
            if token.start >= span.start and token.end <= span.end:
                # The first token in a span is B-, subsequent span tokens are I-.
                prefix = "B" if token.start == span.start else "I"
                return TokenAnnotation(
                    token=token.token,
                    tag=f"{prefix}-{span.entity_type}",
                    start=token.start,
                    end=token.end,
                )
        return token

    @staticmethod
    def _overlaps(start: int, end: int, occupied: list[tuple[int, int]]) -> bool:
        # Half-open interval overlap check for character spans: [start, end).
        return any(start < occupied_end and end > occupied_start for occupied_start, occupied_end in occupied)
