"""Tests for graph builder utilities."""

from engine.graphs.builder import build_graph, build_graph_from_extraction


def test_build_graph_creates_nodes() -> None:
    graph = build_graph([{"id": "n1", "label": "Node 1"}, {"id": "n2", "label": "Node 2"}])
    assert set(graph.nodes.keys()) == {"n1", "n2"}


def test_build_graph_from_extraction_creates_nodes_and_edges() -> None:
    extraction = {
        "entities": [
            {"id": "alice", "label": "Alice", "type": "person"},
            {"id": "acme", "label": "Acme", "type": "org"},
        ],
        "relationships": [
            {"source": "alice", "target": "acme", "relation": "founded"},
        ],
    }
    graph = build_graph_from_extraction(extraction)
    assert set(graph.nodes.keys()) == {"alice", "acme"}
    assert len(graph.edges) == 1
    assert graph.edges[0].source == "alice"
    assert graph.edges[0].target == "acme"
    assert graph.edges[0].relation == "founded"


def test_build_graph_from_extraction_empty_input() -> None:
    graph = build_graph_from_extraction({"entities": [], "relationships": []})
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0
