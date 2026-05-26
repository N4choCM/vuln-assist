"""Prompt templates for grounded vulnerability response generation."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are VulnAssist, a cybersecurity assistant specialized in vulnerability analysis.
Answer the user's question using ONLY the CONTEXT provided below.
Do not invent CVE identifiers, CVSS scores, severities, products, or ATT&CK techniques.
If the context is empty or reports errors, say that vulnerability data could not be retrieved.
Keep answers concise (3 to 5 sentences) and mention the data source when relevant.
"""


def build_user_prompt(*, user_query: str, intent: str, context: str) -> str:
    """Combine the user turn with structured retrieval context."""

    return (
        f"User question: {user_query}\n"
        f"Detected intent: {intent}\n\n"
        f"CONTEXT:\n{context}"
    )
