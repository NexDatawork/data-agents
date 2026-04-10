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
    file_path: str = typer.Argument(
        ...,
        help="Path to the text or PDF file to extract from.",
    ),
    output: str = typer.Option(
        "./output/graph.json",
        "--output",
        "-o",
        help="Destination graph JSON path (default: ./output/graph.json).",
    ),
) -> None:
    """Extract entities and relationships from text/PDF input and emit graph artifacts."""
    # Lazy import keeps CLI startup fast even when engine deps are missing.
    from engine.extractors.text_extractor import (  # noqa: PLC0415
        extract_from_text,
        load_text_source,
        write_extraction_artifacts,
    )

    source = Path(file_path)
    if not source.exists():
        typer.echo(f"Error: file not found: {file_path}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Loading {source}...")
    try:
        text, source_metadata = load_text_source(source)
    except (RuntimeError, ValueError) as exc:
        typer.echo(f"Input error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Extracting graph — calling LLM...")
    try:
        extraction = extract_from_text(text, source_metadata=source_metadata)
        artifacts = write_extraction_artifacts(
            extraction,
            source=source,
            output_path=output,
            title=f"{source_metadata['source_name'].replace('-', ' ').title()} Graph",
        )
    except EnvironmentError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        typer.echo(f"Extraction failed (bad LLM response): {exc}", err=True)
        raise typer.Exit(code=1) from exc

    graph_json = json.dumps(extraction, indent=2)

    typer.echo("\nExtracted graph:")
    typer.echo(graph_json)
    typer.echo(f"\nSaved graph JSON to {artifacts['json_path']}")
    typer.echo(f"Saved graph image to {artifacts['graph_path']}")
