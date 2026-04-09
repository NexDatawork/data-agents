"""Demo command for the OpenGraph AI CLI.

Runs an end-to-end offline pipeline:
    read text file or table folder → extract entities/relationships → build graph → print results.

No API key required.
"""

import json
import re
from pathlib import Path

import typer

from engine.extractors.table_extractor import extract_from_tables
from engine.extractors.table_extractor import extract_from_tables_offline
from engine.extractors.text_extractor import extract_from_text_offline
from engine.graphs.builder import build_graph_from_extraction


def _dataset_name(source: Path) -> str:
    """Return dataset name derived from source folder or file."""
    base = source.name if source.is_dir() else source.stem
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", base).strip("-._")
    return normalized or "dataset"


def _resolve_graph_output_path(source: Path, output: str) -> Path:
    """Place graph JSON inside output/<dataset_name>/ by default."""
    target = Path(output)

    if target.suffix == "":
        return target / _dataset_name(source) / "graph.json"

    if target.parent == Path("output"):
        return target.parent / _dataset_name(source) / target.name

    return target


def demo(
    file_path: str = typer.Argument(
        ...,
        help="Path to a text file, or a folder containing CSV tables.",
    ),
    output: str = typer.Option(
        "./output/graph.json",
        "--output",
        "-o",
        help="Destination file for graph JSON (default: ./output/graph.json).",
    ),
    llm: bool = typer.Option(
        False,
        "--llm",
        help="Use LLM-backed extraction for table folders (requires OPENAI_API_KEY).",
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
            if llm:
                typer.echo("Extracting entities and relationships from tables (LLM mode) ...")
                extraction = extract_from_tables(str(source))
            else:
                typer.echo("Extracting entities and relationships from tables (offline mode) ...")
                extraction = extract_from_tables_offline(str(source))
        except ValueError as exc:
            typer.echo(f"Extraction failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
        except EnvironmentError as exc:
            typer.echo(f"Extraction failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    else:
        typer.echo(f"Reading {source} ...")
        if llm:
            typer.echo(
                "Error: --llm is currently supported only for table folders, not text files.",
                err=True,
            )
            raise typer.Exit(code=1)
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
    graph_json = json.dumps(extraction, indent=2)
    typer.echo(graph_json)

    # ── Persist graph JSON ─────────────────────────────────────────────
    out_path = _resolve_graph_output_path(source, output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(graph_json, encoding="utf-8")
    typer.echo(f"\nSaved graph JSON to {out_path.resolve()}")
