"""Graph container schema.

TODO: Add serialization helpers and graph-level validation.
"""

from dataclasses import dataclass, field

from engine.schema.edge import Edge
from engine.schema.node import Node


@dataclass(slots=True)
class Graph:
    """Represent an in-memory graph.

    TODO: Add indexing for faster lookup and traversal.
    """

    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        """Add or replace a node by ID.

        TODO: Add merge strategy options.
        """
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph.

        TODO: Validate source/target node existence.
        """
        self.edges.append(edge)
