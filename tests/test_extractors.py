"""Tests for text extraction helpers."""

from engine.extractors.text_extractor import extract_text, extract_from_text_offline


def test_extract_text_filters_empty_lines() -> None:
    assert extract_text("A\n\nB\n") == ["A", "B"]


def test_extract_from_text_offline_returns_required_keys() -> None:
    result = extract_from_text_offline("Alice works at Acme.")
    assert "entities" in result
    assert "relationships" in result


def test_extract_from_text_offline_finds_entities() -> None:
    result = extract_from_text_offline("Alice founded Acme Corporation in London.")
    labels = [e["label"] for e in result["entities"]]
    assert "Alice" in labels
    assert "Acme" in labels or "Acme Corporation" in labels


def test_extract_from_text_offline_finds_relationship() -> None:
    result = extract_from_text_offline("Alice founded Acme Corporation.")
    assert any(r["relation"] == "founded" for r in result["relationships"])
