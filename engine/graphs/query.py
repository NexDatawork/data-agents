"""Graph query helpers.

TODO: Provide expressive filtering and traversal APIs.
"""

from engine.schema.graph import Graph


def get_node(graph: Graph, node_id: str):
    """Retrieve one node by ID.

    TODO: Add typed return and missing-node error strategy.
    """
    return graph.nodes.get(node_id)


def neighbors(graph: Graph, node_id: str) -> list[str]:
    """Return neighboring node IDs.

    TODO: Add direction and relation-type filters.
    """
    related: list[str] = []
    for edge in graph.edges:
        if edge.source == node_id:
            related.append(edge.target)
        elif edge.target == node_id:
            related.append(edge.source)
    return related
