"""Text extraction helpers for OpenGraph AI.

Two modes:
- extract_from_text_offline: regex heuristics, no API key needed (demo / tests).
- extract_from_text: LLM-backed, requires OPENAI_API_KEY.

TODO: Replace heuristics with production NLP pipelines.
"""

import json
import re


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def extract_text(raw_text: str) -> list[str]:
    """Return non-empty stripped lines from raw text.

    TODO: Implement semantic chunking and metadata enrichment.
    """
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Offline extraction (no API key required)
# ---------------------------------------------------------------------------

_REL_PATTERN = re.compile(
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)"
    r"\s+(is|was|founded|works at|worked at|leads|acquired)\s+"
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)",
)


def extract_from_text_offline(text: str) -> dict:
    """Extract entities and relationships using regex heuristics.

    No external API or ML model required. Suitable for demos and tests.
    Returns the same shape as extract_from_text:
        {"entities": [...], "relationships": [...]}

    TODO: Improve NER patterns; add co-reference resolution.
    """
    raw_entities = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", text)
    seen: set[str] = set()
    entities: list[dict] = []
    for match in raw_entities:
        slug = match.lower().replace(" ", "-")
        if slug not in seen:
            seen.add(slug)
            entities.append({"id": slug, "label": match, "type": "concept"})

    relationships: list[dict] = []
    for m in _REL_PATTERN.finditer(text):
        src = m.group(1).lower().replace(" ", "-")
        tgt = m.group(3).lower().replace(" ", "-")
        rel = m.group(2)
        relationships.append({"source": src, "target": tgt, "relation": rel})

    return {"entities": entities, "relationships": relationships}


# ---------------------------------------------------------------------------
# LLM-backed extraction (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------

from engine.llm.provider import call_llm  # noqa: E402

_EXTRACTION_PROMPT = (
    "Extract all named entities and relationships from the text below.\n"
    "Return ONLY valid JSON with this exact structure:\n"
    '{{"entities": [{{"id": "<slug>", "label": "<name>", "type": "<person|org|place|concept>"}}], '
    '"relationships": [{{"source": "<id>", "target": "<id>", "relation": "<verb>"}}]}}\n\n'
    "Text:\n{text}"
)


def extract_from_text(text: str) -> dict:
    """Extract entities and relationships from free text via LLM.

    Returns:
        {"entities": [...], "relationships": [...]}

    TODO: Add few-shot examples for improved precision.
    TODO: Add retry logic with back-off on transient API failures.
    TODO: Validate returned structure with a Pydantic model.
    """
    prompt = _EXTRACTION_PROMPT.format(text=text)
    raw = call_llm(prompt)

    # Strip markdown code fences the model may wrap around JSON.
    clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean.strip(), flags=re.MULTILINE)

    try:
        result = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned non-JSON output: {exc}\nRaw response:\n{raw}"
        ) from exc

    if "entities" not in result or "relationships" not in result:
        raise ValueError(
            "LLM response missing required keys 'entities' or 'relationships'."
        )

    return result
