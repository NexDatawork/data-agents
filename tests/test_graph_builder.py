"""Tests for graph builder stubs.

TODO: Add tests for edge creation and duplicate handling.
"""

from engine.graphs.builder import build_graph


def test_build_graph_creates_nodes() -> None:
    """Ensure graph builder creates nodes from input records.

    TODO: Validate behavior for missing IDs and labels.
    """
    graph = build_graph([{"id": "n1", "label": "Node 1"}, {"id": "n2", "label": "Node 2"}])
    assert set(graph.nodes.keys()) == {"n1", "n2"}
