"""Visualization command for the OpenGraph AI CLI."""

from pathlib import Path

import typer

from engine.extractors.table_extractor import extract_from_tables_offline
from engine.extractors.text_extractor import extract_from_text_offline
from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.visualize import visualize_graph, visualize_schema_graph


def visualize(
    file_path: str = typer.Argument(
        ...,
        help="Path to a text file, or a folder containing CSV tables.",
    ),
    output: str = typer.Option(
        "./output/graph.png",
        "--output",
        "-o",
        help="Destination image path (default: ./output/graph.png).",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="Optional chart title.",
    ),
    schema_view: bool = typer.Option(
        False,
        "--schema-view",
        help="Render a high-level entity/table graph instead of every row-level node.",
    ),
) -> None:
    """Build a graph from input data and save a human-readable image."""
    source = Path(file_path)
    if not source.exists():
        typer.echo(f"Error: file not found — {file_path}", err=True)
        raise typer.Exit(code=1)

    if source.is_dir():
        typer.echo(f"Reading table folder {source} ...")
        try:
            extraction = extract_from_tables_offline(str(source))
        except ValueError as exc:
            typer.echo(f"Extraction failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    else:
        typer.echo(f"Reading {source} ...")
        text = source.read_text(encoding="utf-8")
        extraction = extract_from_text_offline(text)

    graph = build_graph_from_extraction(extraction)

    try:
        render = visualize_schema_graph if schema_view else visualize_graph
        saved_path = render(graph, output, title=title)
    except ValueError as exc:
        typer.echo(f"Visualization failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Saved graph image to {saved_path}")
