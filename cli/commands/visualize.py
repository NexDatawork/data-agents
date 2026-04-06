"""Visualization command for the OpenGraph AI CLI."""

from pathlib import Path
import re

import typer

from engine.extractors.table_extractor import extract_from_tables_offline
from engine.extractors.text_extractor import extract_from_text_offline
from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.visualize import visualize_graph, visualize_schema_graph


def _dataset_name(source: Path) -> str:
    """Return dataset name derived from source folder or file."""
    base = source.name if source.is_dir() else source.stem
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", base).strip("-._")
    return normalized or "dataset"


def _resolve_output_path(source: Path, output: str) -> Path:
    """Place visualization outputs inside output/<dataset_name>/ by default."""
    target = Path(output)

    # If a directory is passed, use default filename inside dataset folder.
    if target.suffix == "":
        return target / _dataset_name(source) / "graph.png"

    # If output points directly under ./output, insert dataset subfolder.
    if target.parent == Path("output"):
        return target.parent / _dataset_name(source) / target.name

    return target


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
    final_output = _resolve_output_path(source, output)

    try:
        render = visualize_schema_graph if schema_view else visualize_graph
        saved_path = render(graph, str(final_output), title=title)
    except ValueError as exc:
        typer.echo(f"Visualization failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Saved graph image to {saved_path}")
