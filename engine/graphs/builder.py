"""Graph construction utilities.

TODO: Convert extracted entities into connected graph structures.
"""

from collections.abc import Iterable

from engine.schema.graph import Graph
from engine.schema.node import Node


def build_graph(records: Iterable[dict[str, str]]) -> Graph:
    """Build a graph from iterable records.

    TODO: Add edge generation logic from record relationships.
    """
    graph = Graph()
    for index, record in enumerate(records, start=1):
        node_id = record.get("id", f"node-{index}")
        label = record.get("label", node_id)
        graph.add_node(Node(id=node_id, label=label, properties=dict(record)))
    return graph
