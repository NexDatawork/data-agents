"""Tests for graph visualization helpers."""

from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.visualize import visualize_graph, visualize_schema_graph


def test_visualize_graph_writes_png(tmp_path) -> None:
    extraction = {
        "entities": [
            {"id": "customers:c001", "label": "Alice Chen", "type": "customer"},
            {"id": "orders:o1001", "label": "O1001", "type": "order"},
        ],
        "relationships": [
            {"source": "orders:o1001", "target": "customers:c001", "relation": "customer"},
        ],
    }
    graph = build_graph_from_extraction(extraction)

    output_path = tmp_path / "graph.png"
    saved_path = visualize_graph(graph, str(output_path), title="Example Graph")

    assert saved_path == output_path.resolve()
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_visualize_schema_graph_writes_png(tmp_path) -> None:
    extraction = {
        "entities": [
            {"id": "customers:c001", "label": "Alice Chen", "type": "customer", "properties": {"table": "customers"}},
            {"id": "orders:o1001", "label": "O1001", "type": "order", "properties": {"table": "orders"}},
            {"id": "payments:p001", "label": "P001", "type": "payment", "properties": {"table": "payments"}},
        ],
        "relationships": [
            {"source": "orders:o1001", "target": "customers:c001", "relation": "for_customer"},
            {"source": "payments:p001", "target": "orders:o1001", "relation": "for_order"},
        ],
    }
    graph = build_graph_from_extraction(extraction)

    output_path = tmp_path / "schema-graph.png"
    saved_path = visualize_schema_graph(graph, str(output_path), title="Schema Graph")

    assert saved_path == output_path.resolve()
    assert output_path.exists()
    assert output_path.stat().st_size > 0
