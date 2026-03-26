"""Graph construction utilities.

TODO: Convert extracted entities into connected graph structures.
"""

from collections.abc import Iterable

from engine.schema.edge import Edge
from engine.schema.graph import Graph
from engine.schema.node import Node


def build_graph(records: Iterable[dict[str, str]]) -> Graph:
    """Build a graph from iterable records (nodes only).

    TODO: Add edge generation logic from record relationships.
    """
    graph = Graph()
    for index, record in enumerate(records, start=1):
        node_id = record.get("id", f"node-{index}")
        label = record.get("label", node_id)
        graph.add_node(Node(id=node_id, label=label, properties=dict(record)))
    return graph


def build_graph_from_extraction(extraction: dict) -> Graph:
    """Build a graph from the dict returned by extract_from_text / extract_from_text_offline.

    Expected shape:
        {
            "entities":      [{"id": ..., "label": ..., "type": ...}, ...],
            "relationships": [{"source": ..., "target": ..., "relation": ...}, ...],
        }
    """
    graph = Graph()

    for ent in extraction.get("entities", []):
        graph.add_node(
            Node(
                id=ent["id"],
                label=ent["label"],
                properties={"type": ent.get("type", "")},
            )
        )

    for rel in extraction.get("relationships", []):
        graph.add_edge(
            Edge(
                source=rel["source"],
                target=rel["target"],
                relation=rel["relation"],
            )
        )

    return graph
