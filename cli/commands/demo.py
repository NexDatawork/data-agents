"""Demo command for the OpenGraph AI CLI.

Runs an end-to-end offline pipeline:
    read text file or table folder → extract entities/relationships → build graph → print results.

No API key required.
"""

import json
from pathlib import Path

import typer

from engine.extractors.table_extractor import extract_from_tables_offline
from engine.extractors.text_extractor import extract_from_text_offline
from engine.graphs.builder import build_graph_from_extraction


def demo(
    file_path: str = typer.Argument(
        ...,
        help="Path to a text file, or a folder containing CSV tables.",
    ),
) -> None:
    """Read text or table input, extract entities, build a graph, and print nodes + edges."""
    source = Path(file_path)
    if not source.exists():
        typer.echo(f"Error: file not found — {file_path}", err=True)
        raise typer.Exit(code=1)

    if source.is_dir():
        typer.echo(f"Reading table folder {source} ...")
        try:
            typer.echo("Extracting entities and relationships from tables (offline mode) ...")
            extraction = extract_from_tables_offline(str(source))
        except ValueError as exc:
            typer.echo(f"Extraction failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    else:
        typer.echo(f"Reading {source} ...")
        text = source.read_text(encoding="utf-8")
        typer.echo("Extracting entities and relationships (offline mode) ...")
        extraction = extract_from_text_offline(text)

    typer.echo("Building graph ...")
    graph = build_graph_from_extraction(extraction)

    # ── Print nodes ───────────────────────────────────────────────────
    typer.echo(f"\nNodes ({len(graph.nodes)}):")
    for node in graph.nodes.values():
        node_type = node.properties.get("type", "?")
        typer.echo(f"  [{node.id}]  {node.label}  <{node_type}>")

    # ── Print edges ───────────────────────────────────────────────────
    typer.echo(f"\nEdges ({len(graph.edges)}):")
    if graph.edges:
        for edge in graph.edges:
            typer.echo(f"  {edge.source}  --[{edge.relation}]-->  {edge.target}")
    else:
        typer.echo("  (none detected)")

    # ── Print final graph JSON ────────────────────────────────────────
    typer.echo("\nGraph JSON:")
    typer.echo(json.dumps(extraction, indent=2))
