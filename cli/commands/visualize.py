"""Visualization command for the OpenGraph AI CLI."""

import json
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


def _default_graph_json_path(source: Path, output_root: str) -> Path:
    """Return default saved graph JSON path for a dataset source."""
    return Path(output_root) / _dataset_name(source) / "graph.json"


def _load_extraction_json(graph_path: Path) -> dict:
    """Load extraction JSON from disk and validate required keys."""
    try:
        payload = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Saved graph file is not valid JSON: {graph_path}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"Saved graph file has invalid structure: {graph_path}")
    if "entities" not in payload or "relationships" not in payload:
        raise ValueError(
            f"Saved graph file missing 'entities'/'relationships': {graph_path}"
        )

    return payload


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
    output_root: str = typer.Option(
        "./output",
        "--output-root",
        help="Root folder containing saved dataset graph JSON files.",
    ),
    rebuild: bool = typer.Option(
        False,
        "--rebuild",
        help="Rebuild graph from source files instead of loading from output folder.",
    ),
) -> None:
    """Render a saved graph image, or rebuild from source when requested."""
    source = Path(file_path)
    if not source.exists():
        typer.echo(f"Error: file not found — {file_path}", err=True)
        raise typer.Exit(code=1)

    saved_graph_path = _default_graph_json_path(source, output_root)

    if rebuild:
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

        saved_graph_path.parent.mkdir(parents=True, exist_ok=True)
        saved_graph_path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")
        typer.echo(f"Saved rebuilt graph JSON to {saved_graph_path.resolve()}")
    else:
        if not saved_graph_path.exists():
            typer.echo(
                (
                    "Error: no saved graph JSON found for this dataset. "
                    f"Expected: {saved_graph_path}\n"
                    "Run demo first to persist graph JSON, or pass --rebuild."
                ),
                err=True,
            )
            raise typer.Exit(code=1)
        try:
            extraction = _load_extraction_json(saved_graph_path)
        except ValueError as exc:
            typer.echo(f"Error loading saved graph: {exc}", err=True)
            raise typer.Exit(code=1) from exc

        typer.echo(f"Loaded saved graph JSON from {saved_graph_path.resolve()}")

    graph = build_graph_from_extraction(extraction)
    final_output = _resolve_output_path(source, output)

    try:
        render = visualize_schema_graph if schema_view else visualize_graph
        saved_path = render(graph, str(final_output), title=title)
    except ValueError as exc:
        typer.echo(f"Visualization failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Saved graph image to {saved_path}")
