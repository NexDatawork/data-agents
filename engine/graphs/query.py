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


def find_nodes(graph: Graph, term: str, exact: bool = False) -> list[str]:
    """Find node IDs by matching a search term against node ID or label.

    Args:
        graph: The graph to search.
        term: Search term.
        exact: If True, require exact equality. Otherwise use substring match.

    Returns:
        List of matching node IDs.
    """
    needle = term.strip().lower()
    if not needle:
        return []

    matches: list[str] = []
    for node in graph.nodes.values():
        node_id_l = node.id.lower()
        label_l = node.label.lower()
        if exact:
            ok = needle == node_id_l or needle == label_l
        else:
            ok = needle in node_id_l or needle in label_l
        if ok:
            matches.append(node.id)
    return matches


def relations_for_node(graph: Graph, node_id: str) -> list[str]:
    """Return readable relation lines touching a node.

    Format:
        "<source> --[<relation>]--> <target>"
    """
    lines: list[str] = []
    for edge in graph.edges:
        if edge.source == node_id or edge.target == node_id:
            lines.append(f"{edge.source} --[{edge.relation}]--> {edge.target}")
    return lines


def query_graph(graph: Graph, term: str, exact: bool = False) -> list[dict[str, object]]:
    """Query graph nodes by term and return structured neighbor + relation info.

    Returns:
        [
            {
                "id": "...",
                "label": "...",
                "type": "...",
                "neighbors": [{"id": "...", "label": "..."}, ...],
                "relations": ["a --[rel]--> b", ...],
            },
            ...
        ]
    """
    results: list[dict[str, object]] = []
    for node_id in find_nodes(graph, term=term, exact=exact):
        node = get_node(graph, node_id)
        if node is None:
            continue

        neighbor_items: list[dict[str, str]] = []
        for nbr_id in neighbors(graph, node_id):
            nbr = get_node(graph, nbr_id)
            neighbor_items.append({"id": nbr_id, "label": nbr.label if nbr else "?"})

        results.append(
            {
                "id": node.id,
                "label": node.label,
                "type": node.properties.get("type", ""),
                "neighbors": neighbor_items,
                "relations": relations_for_node(graph, node_id),
            }
        )

    return results
