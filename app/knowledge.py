"""
Knowledge base for the sleep-company AI agent.

Plain idea: the agent should answer from approved company documents,
not from imagination.

Technical idea: a tiny retrieval module. We load markdown files from
data/knowledge/, split them into titled sections, and return the sections
that best match the customer's question (simple keyword scoring for now).

This is step one toward RAG (Retrieval-Augmented Generation): this file
*retrieves* approved sections; responses.py turns them into customer language.
Later an AI can rewrite those same sections without changing retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "knowledge"

# Words too common to signal meaning; ignored when scoring matches.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "be", "been", "do", "does", "did",
    "i", "my", "me", "we", "you", "your", "it", "its", "of", "to", "in", "on",
    "for", "and", "or", "with", "what", "how", "can", "about", "have", "has",
}


@dataclass
class Snippet:
    """One titled section from one knowledge document."""

    document: str      # e.g. "Product Guide"
    section: str       # e.g. "CloudRest Pillow"
    content: str       # the section text
    source_file: str   # e.g. "products.md"


def _words(text: str) -> set[str]:
    """Break text into lowercase words, dropping stopwords and single letters."""
    tokens = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 1}


def _load_snippets() -> list[Snippet]:
    """
    Read every markdown file in data/knowledge/ and split it into sections.

    Convention: "# Title" names the document, "## Heading" starts a section.
    """
    snippets: list[Snippet] = []
    if not KNOWLEDGE_DIR.exists():
        return snippets

    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        document = path.stem.replace("-", " ").title()
        section = "Introduction"
        lines: list[str] = []

        # The sentinel heading flushes the final section of each file.
        for line in path.read_text(encoding="utf-8").splitlines() + ["## _end_"]:
            if line.startswith("# ") and not line.startswith("## "):
                document = line[2:].strip()
            elif line.startswith("## "):
                content = "\n".join(lines).strip()
                if content:
                    snippets.append(Snippet(document, section, content, path.name))
                section = line[3:].strip()
                lines = []
            else:
                lines.append(line)

    return snippets


def search_knowledge(
    question: str, limit: int = 2, prefer_file: str | None = None
) -> list[Snippet]:
    """
    Return the best-matching sections for a question (possibly none).

    prefer_file lets the caller use what it already knows. Example: the
    classifier said this is sleep guidance, so answer from sleep-tips.md
    when that file has any match, instead of a policy that happens to share
    words like "sleep" and "night".
    """
    question_words = _words(question)
    if not question_words:
        return []

    scored: list[tuple[int, Snippet]] = []
    for snippet in _load_snippets():
        overlap = len(question_words & _words(snippet.content))
        # Heading words count double: matching a section title is a strong signal.
        title_bonus = 2 * len(
            question_words & (_words(snippet.section) | _words(snippet.document))
        )
        score = overlap + title_bonus
        if score > 0:
            scored.append((score, snippet))

    if prefer_file:
        preferred = [pair for pair in scored if pair[1].source_file == prefer_file]
        if preferred:
            scored = preferred

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [snippet for _, snippet in scored[:limit]]
