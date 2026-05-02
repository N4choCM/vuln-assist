"""Controlled, rule-based paraphrasing for query templates."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParaphraseRule:
    """A meaning-preserving phrase replacement."""

    pattern: str
    replacements: tuple[str, ...]


class RuleBasedParaphraser:
    """Apply deterministic rule families without using uncontrolled generation."""

    def __init__(self) -> None:
        # Regex word boundaries avoid replacing substrings inside longer words.
        self._rules = (
            ParaphraseRule(r"\bWhat is\b", ("What can you tell me about", "Define")),
            ParaphraseRule(r"\bGive me\b", ("Provide", "Show me")),
            ParaphraseRule(r"\bShow\b", ("List", "Display")),
            ParaphraseRule(r"\bFind\b", ("Search for", "Show me")),
            ParaphraseRule(r"\bList\b", ("Show", "Give me")),
            ParaphraseRule(r"\bCheck\b", ("Look up", "Verify")),
            ParaphraseRule(r"\bvulnerabilities\b", ("CVEs", "security vulnerabilities")),
            ParaphraseRule(r"\bvulnerability\b", ("security flaw", "CVE entry")),
            ParaphraseRule(r"\bimpact\b", ("affect", "apply to")),
            ParaphraseRule(r"\baffecting\b", ("impacting", "related to")),
            ParaphraseRule(r"\bseverity\b", ("risk level", "severity rating")),
            ParaphraseRule(r"\bknown CVEs\b", ("documented CVEs", "reported CVEs")),
        )

    def paraphrase(self, text: str, rng: random.Random, max_replacements: int = 2) -> str:
        """Return a controlled paraphrase of a template string."""

        # Only rules that match the current template are candidates for replacement.
        candidates = [rule for rule in self._rules if re.search(rule.pattern, text)]
        # Shuffle candidate order to vary outputs while remaining seed-controlled.
        rng.shuffle(candidates)

        rewritten = text
        replacements_applied = 0
        for rule in candidates:
            replacement = rng.choice(rule.replacements)
            # subn returns both the rewritten text and whether a replacement occurred.
            rewritten, count = re.subn(rule.pattern, replacement, rewritten, count=1)
            if count:
                replacements_applied += 1
            # Keep paraphrases conservative so the original intent stays unambiguous.
            if replacements_applied >= max_replacements:
                break

        return self._clean(rewritten)

    @staticmethod
    def _clean(text: str) -> str:
        # Normalize whitespace and fix punctuation artifacts introduced by replacements.
        cleaned = re.sub(r"\s+", " ", text).strip()
        cleaned = cleaned.replace("?.", "?").replace("..", ".")
        return cleaned
