"""Tests for extraction stubs.

TODO: Add parameterized tests for malformed and edge-case input.
"""

from engine.extractors.text_extractor import extract_text


def test_extract_text_filters_empty_lines() -> None:
    """Validate placeholder text extraction behavior.

    TODO: Add coverage for Unicode and long documents.
    """
    assert extract_text("A\n\nB\n") == ["A", "B"]
