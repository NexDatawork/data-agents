"""Text extraction helpers for OpenGraph AI.

TODO: Replace placeholder parsing with production NLP pipelines.
"""


def extract_text(raw_text: str) -> list[str]:
    """Extract normalized text chunks from raw text input.

    TODO: Implement semantic chunking and metadata enrichment.
    """
    return [line.strip() for line in raw_text.splitlines() if line.strip()]
