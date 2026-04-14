"""Tests for CLI graph cache path and loading helpers."""

import json
from pathlib import Path

import pytest

from cli.commands.demo import _resolve_graph_output_path
from cli.commands.query import _default_graph_json_path, _load_extraction_json


def test_demo_resolve_graph_output_path_inserts_dataset_folder() -> None:
    source = Path("examples/table_example")
    resolved = _resolve_graph_output_path(source, "output/graph.json")
    assert resolved == Path("output/table_example/graph.json")


def test_query_default_graph_json_path_uses_dataset_folder() -> None:
    source = Path("examples/text_example.txt")
    resolved = _default_graph_json_path(source, "output")
    assert resolved == Path("output/text_example/graph.json")


def test_load_extraction_json_reads_valid_payload(tmp_path: Path) -> None:
    payload = {
        "entities": [{"id": "n1", "label": "Node", "type": "concept"}],
        "relationships": [],
    }
    graph_file = tmp_path / "graph.json"
    graph_file.write_text(json.dumps(payload), encoding="utf-8")

    loaded = _load_extraction_json(graph_file)
    assert loaded == payload


def test_load_extraction_json_rejects_invalid_payload(tmp_path: Path) -> None:
    bad_file = tmp_path / "graph.json"
    bad_file.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError):
        _load_extraction_json(bad_file)
