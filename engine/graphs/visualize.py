"""Graph visualization helpers.

Render in-memory graphs to static image files for quick human inspection.
"""

from collections.abc import Iterable
from math import sqrt
from pathlib import Path
from textwrap import fill

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from engine.schema.graph import Graph

_TYPE_COLORS = (
    "#6C63FF",
    "#2A9D8F",
    "#E76F51",
    "#F4A261",
    "#457B9D",
    "#A8DADC",
    "#8D99AE",
    "#EF476F",
)


def _humanize(value: str) -> str:
    """Convert identifiers into human-readable labels."""
    normalized = value.replace("__", " ").replace("_", " ").replace("-", " ").strip()
    if not normalized:
        return "Unknown"
    return " ".join(part.capitalize() for part in normalized.split())


def _truncate_label(label: str, max_length: int = 20) -> str:
    """Shorten labels so dense graphs remain readable."""
    if len(label) <= max_length:
        return label
    return f"{label[: max_length - 1]}…"


def _type_color_map(node_types: Iterable[str]) -> dict[str, str]:
    """Assign deterministic colors to node types."""
    normalized = sorted({node_type or "unknown" for node_type in node_types})
    return {
        node_type: _TYPE_COLORS[index % len(_TYPE_COLORS)]
        for index, node_type in enumerate(normalized)
    }


def _group_key(node_id: str, node_data: dict[str, str]) -> str:
    """Return the schema-level grouping key for a node."""
    table_name = node_data.get("table") or node_data.get("source_table")
    node_type = node_data.get("type")
    if table_name:
        return table_name
    if node_type:
        return node_type
    if ":" in node_id:
        return node_id.split(":", maxsplit=1)[0]
    return node_id


def _render_schema_graph(graph: Graph) -> nx.DiGraph:
    """Collapse a detailed graph into a schema/entity-type graph."""
    rendered = nx.DiGraph()
    node_to_group: dict[str, str] = {}

    for node_id, node in graph.nodes.items():
        group = _group_key(node_id, node.properties)
        node_to_group[node_id] = group

        if not rendered.has_node(group):
            rendered.add_node(
                group,
                label=_humanize(group),
                node_type=node.properties.get("type", group),
                member_count=0,
            )

        rendered.nodes[group]["member_count"] += 1

    edge_labels: dict[tuple[str, str], set[str]] = {}
    for edge in graph.edges:
        source_group = node_to_group.get(edge.source)
        target_group = node_to_group.get(edge.target)
        if not source_group or not target_group or source_group == target_group:
            continue

        key = (source_group, target_group)
        edge_labels.setdefault(key, set()).add(edge.relation)

    for (source_group, target_group), relations in sorted(edge_labels.items()):
        rendered.add_edge(
            source_group,
            target_group,
            relation=" / ".join(sorted(_humanize(relation).upper() for relation in relations)),
        )

    return rendered


def visualize_graph(
    graph: Graph,
    output_path: str,
    *,
    title: str | None = None,
    layout_seed: int = 42,
) -> Path:
    """Render a graph to a PNG image and return the saved path."""
    if not graph.nodes:
        raise ValueError("Cannot visualize an empty graph.")

    rendered = nx.MultiDiGraph()
    for node in graph.nodes.values():
        rendered.add_node(
            node.id,
            label=node.label,
            node_type=node.properties.get("type", "unknown"),
        )

    for edge in graph.edges:
        rendered.add_edge(edge.source, edge.target, relation=edge.relation)

    node_count = len(graph.nodes)
    edge_count = len(graph.edges)
    figure_width = max(10.0, min(24.0, 8.0 + sqrt(node_count) * 2.2))
    figure_height = max(8.0, min(20.0, 6.0 + sqrt(max(node_count, edge_count + 1)) * 2.0))

    plt.figure(figsize=(figure_width, figure_height))
    position = nx.spring_layout(rendered, seed=layout_seed, k=1.8 / sqrt(max(node_count, 1)))

    type_lookup = {
        node_id: data.get("node_type", "unknown")
        for node_id, data in rendered.nodes(data=True)
    }
    color_map = _type_color_map(type_lookup.values())
    node_colors = [color_map[type_lookup[node_id]] for node_id in rendered.nodes]
    node_sizes = [1400 if rendered.degree(node_id) <= 2 else 1800 for node_id in rendered.nodes]

    nx.draw_networkx_nodes(
        rendered,
        position,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.94,
        linewidths=1.2,
        edgecolors="#1F2937",
    )
    nx.draw_networkx_edges(
        rendered,
        position,
        arrowstyle="-|>",
        arrowsize=16,
        width=1.4,
        edge_color="#7C8798",
        connectionstyle="arc3,rad=0.08",
        alpha=0.75,
    )
    nx.draw_networkx_labels(
        rendered,
        position,
        labels={
            node_id: _truncate_label(data.get("label", node_id))
            for node_id, data in rendered.nodes(data=True)
        },
        font_size=9,
        font_weight="bold",
        font_color="#111827",
    )

    if edge_count <= 40:
        nx.draw_networkx_edge_labels(
            rendered,
            position,
            edge_labels={
                (source, target, key): _truncate_label(data.get("relation", ""), 18)
                for source, target, key, data in rendered.edges(keys=True, data=True)
            },
            font_size=7,
            font_color="#374151",
            rotate=False,
            label_pos=0.5,
        )

    legend_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label=node_type,
            markerfacecolor=color,
            markeredgecolor="#1F2937",
            markersize=10,
        )
        for node_type, color in color_map.items()
    ]
    if legend_handles:
        plt.legend(
            handles=legend_handles,
            title="Node types",
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            borderaxespad=0.0,
            frameon=False,
        )

    plt.title(title or "OpenGraph AI Graph View", fontsize=14, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(destination, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    return destination.resolve()


def visualize_schema_graph(
    graph: Graph,
    output_path: str,
    *,
    title: str | None = None,
    layout_seed: int = 42,
) -> Path:
    """Render a schema/entity-type view of the graph to a PNG image."""
    if not graph.nodes:
        raise ValueError("Cannot visualize an empty graph.")

    rendered = _render_schema_graph(graph)
    if not rendered.nodes:
        raise ValueError("Cannot build a schema graph from the provided data.")

    node_count = len(rendered.nodes)
    plt.figure(figsize=(10, max(8.0, min(14.0, 6.0 + node_count * 0.9))))
    position = nx.spring_layout(rendered, seed=layout_seed, k=1.7 / sqrt(max(node_count, 1)))

    nx.draw_networkx_nodes(
        rendered,
        position,
        node_color="#FFFFFF",
        node_size=2200,
        alpha=0.98,
        linewidths=1.4,
        edgecolors="#A8B0BB",
    )
    nx.draw_networkx_edges(
        rendered,
        position,
        arrowstyle="-|>",
        arrowsize=18,
        width=1.3,
        edge_color="#B0B8C4",
        connectionstyle="arc3,rad=0.06",
        alpha=0.9,
    )
    nx.draw_networkx_labels(
        rendered,
        position,
        labels={
            node_id: fill(data.get("label", node_id), width=10)
            for node_id, data in rendered.nodes(data=True)
        },
        font_size=9,
        font_weight="medium",
        font_color="#374151",
    )
    nx.draw_networkx_edge_labels(
        rendered,
        position,
        edge_labels={
            (source, target): _truncate_label(data.get("relation", ""), 26)
            for source, target, data in rendered.edges(data=True)
        },
        font_size=7,
        font_color="#9AA3AF",
        rotate=True,
        label_pos=0.5,
    )

    plt.title(title or "OpenGraph AI Schema View", fontsize=14, fontweight="bold")
    plt.axis("off")
    plt.tight_layout()

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(destination, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()
    return destination.resolve()
