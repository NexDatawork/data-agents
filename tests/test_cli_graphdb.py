"""Tests for graphdb CLI commands and Neo4j payload helpers."""

import json
from pathlib import Path

from click.testing import CliRunner
from typer.main import get_command

from cli.__main__ import app as cli_app
from cli.commands.graphdb import _dataset_name_from_json_path
from engine.connectors.neo4j_aura import _sanitize_node_properties
from engine.connectors.neo4j_aura import _sanitize_relationship_properties


runner = CliRunner()


def test_dataset_name_from_graph_json_parent() -> None:
    path = Path("output/Airline-Loyalty-Program/graph.json")
    assert _dataset_name_from_json_path(path) == "Airline-Loyalty-Program"


def test_sanitize_node_properties_excludes_structural_fields() -> None:
    entity = {
        "id": "n1",
        "label": "Alice",
        "type": "person",
        "dataset": "demo",
        "confidence": 0.91,
        "properties": {"source": "llm", "dataset": "bad"},
    }

    props = _sanitize_node_properties(entity)

    assert props["source"] == "llm"
    assert props["confidence"] == 0.91
    assert "dataset" not in props


def test_sanitize_relationship_properties_excludes_structural_fields() -> None:
    relationship = {
        "source": "n1",
        "target": "n2",
        "relation": "founded",
        "score": 0.5,
        "properties": {"evidence": "text", "dataset": "bad"},
    }

    props = _sanitize_relationship_properties(relationship)

    assert props["evidence"] == "text"
    assert props["score"] == 0.5
    assert "dataset" not in props


def test_graphdb_push_uses_dataset_and_calls_store(monkeypatch, tmp_path: Path) -> None:
    graph_path = tmp_path / "output" / "DemoSet" / "graph.json"
    graph_path.parent.mkdir(parents=True)
    graph_path.write_text(
        json.dumps({"entities": [{"id": "n1", "label": "Node"}], "relationships": []}),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_store(extraction: dict, *, dataset: str, clear_existing: bool):
        captured["extraction"] = extraction
        captured["dataset"] = dataset
        captured["clear_existing"] = clear_existing
        return {"node_count": 1, "edge_count": 0}

    monkeypatch.setattr("cli.commands.graphdb.store_extraction_in_neo4j", fake_store)

    result = runner.invoke(
        get_command(cli_app),
        ["graphdb", "push", str(graph_path)],
    )

    assert result.exit_code == 0, result.stdout
    assert captured["dataset"] == "DemoSet"
    assert captured["clear_existing"] is True


def test_graphdb_pull_writes_output(monkeypatch, tmp_path: Path) -> None:
    def fake_export(*, dataset: str):
        assert dataset == "DemoSet"
        return {
            "entities": [{"id": "n1", "label": "Node", "type": "concept"}],
            "relationships": [],
            "metadata": {"dataset": dataset},
        }

    monkeypatch.setattr("cli.commands.graphdb.export_extraction_from_neo4j", fake_export)
    monkeypatch.setattr(
        "cli.commands.graphdb.build_graph_from_extraction",
        lambda extraction: extraction,
    )

    def fake_visualize(graph: dict, output_path: str, *, title: str | None = None):
        del graph, title
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"fake-png")
        return out.resolve()

    monkeypatch.setattr("cli.commands.graphdb.visualize_graph", fake_visualize)

    out_path = tmp_path / "output" / "graph.json"
    result = runner.invoke(
        get_command(cli_app),
        ["graphdb", "pull", "DemoSet", "--output", str(out_path)],
    )

    assert result.exit_code == 0, result.stdout
    expected = out_path
    assert expected.exists()
    assert (out_path.parent / "graph.png").exists()

    payload = json.loads(expected.read_text(encoding="utf-8"))
    assert payload["metadata"]["dataset"] == "DemoSet"
    assert "JSON:" in result.stdout
    assert "PNG:" in result.stdout
