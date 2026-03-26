"""CLI extract subcommands for OpenGraph AI.

Usage:
    python -m cli extract text <file>
"""

import json
from pathlib import Path

import typer

app = typer.Typer(help="Extract graph structures from various data sources.")


@app.command("text")
def extract_text(
    file_path: str = typer.Argument(..., help="Path to the text file to extract from."),
    output: str = typer.Option(
        "./output/graph.json",
        "--output",
        "-o",
        help="Destination file for the graph JSON (default: ./output/graph.json).",
    ),
) -> None:
    """Extract entities and relationships from a text file and emit graph JSON.

    Reads the file at FILE_PATH, sends its content to the LLM-backed extractor,
    prints the resulting graph JSON, and saves it to OUTPUT.
    """
    # Lazy import keeps CLI startup fast even when engine deps are missing.
    from engine.extractors.text_extractor import extract_from_text  # noqa: PLC0415

    source = Path(file_path)
    if not source.exists():
        typer.echo(f"Error: file not found: {file_path}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Reading {source}...")
    text = source.read_text(encoding="utf-8")

    typer.echo("Extracting graph — calling LLM...")
    try:
        graph = extract_from_text(text)
    except EnvironmentError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(code=1)
    except ValueError as exc:
        typer.echo(f"Extraction failed (bad LLM response): {exc}", err=True)
        raise typer.Exit(code=1)

    graph_json = json.dumps(graph, indent=2)

    # ── Print to console ──────────────────────────────────────────────
    typer.echo("\nExtracted graph:")
    typer.echo(graph_json)

    # ── Persist to disk ───────────────────────────────────────────────
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(graph_json, encoding="utf-8")
    typer.echo(f"\nSaved to {out_path.resolve()}")
