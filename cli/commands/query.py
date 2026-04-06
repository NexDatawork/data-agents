"""Query command for the OpenGraph AI CLI.

Reads a saved graph JSON by default and queries it by term.
"""

import json
import re
from pathlib import Path

import typer

from engine.extractors.table_extractor import extract_from_tables_offline
from engine.extractors.text_extractor import extract_from_text_offline
from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.query import query_graph


def _dataset_name(source: Path) -> str:
    """Return dataset name derived from source folder or file."""
    base = source.name if source.is_dir() else source.stem
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", base).strip("-._")
    return normalized or "dataset"


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


def query(
    file_path: str = typer.Argument(
        ...,
        help="Path to a text file, or a folder containing CSV tables.",
    ),
    term: str = typer.Argument(
        ...,
        help="Search term, e.g. 'alice'.",
    ),
    exact: bool = typer.Option(
        False,
        "--exact",
        help="Match term exactly against node label or id.",
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
    """Query graph nodes and print matches, neighbors, and relations."""
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
    results = query_graph(graph, term=term, exact=exact)

    if not results:
        typer.echo(f"No matches found for '{term}'.")
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(results)} match(es) for '{term}':")
    for item in results:
        typer.echo(f"\n[{item['id']}]  {item['label']}  <{item['type'] or '?'}>")

        neighbors = item["neighbors"]
        if neighbors:
            typer.echo("  Neighbors:")
            for nbr in neighbors:
                typer.echo(f"    - {nbr['id']} ({nbr['label']})")
        else:
            typer.echo("  Neighbors: (none)")

        relations = item["relations"]
        if relations:
            typer.echo("  Relations:")
            for line in relations:
                typer.echo(f"    - {line}")
        else:
            typer.echo("  Relations: (none)")
