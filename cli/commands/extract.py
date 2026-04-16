"""CLI extract subcommands for OpenGraph AI.

Usage:
    python -m cli extract text <file>
"""

import json
import os
import re
from pathlib import Path

import typer

from engine.config import load_env_config
from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.visualize import visualize_graph
from engine.upload.gcp import DEFAULT_GCS_PREFIX
from engine.upload.gcp import upload_dataset_to_gcs

app = typer.Typer(help="Extract graph structures from various data sources.")


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


def _resolve_dataset_folder(dataset_name: str, input_root: str) -> Path:
    """Resolve a dataset folder by name from within the input root."""
    root = Path(input_root)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Input root not found: {root}")

    matches = sorted(
        path for path in root.rglob("*") if path.is_dir() and path.name == dataset_name
    )
    if not matches:
        raise ValueError(f"Dataset folder '{dataset_name}' was not found under {root}")
    if len(matches) > 1:
        options = ", ".join(str(path) for path in matches)
        raise ValueError(
            f"Multiple dataset folders named '{dataset_name}' were found under {root}: {options}"
        )

    return matches[0]


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


@app.command("tables-gcs")
def extract_tables_gcs(
    dataset_name: str = typer.Argument(
        ...,
        help="Dataset folder name under input/ to upload and extract from GCS.",
    ),
    input_root: str = typer.Option(
        "./input",
        "--input-root",
        help="Root folder containing local dataset directories.",
    ),
    output: str = typer.Option(
        "./output/graph.json",
        "--output",
        "-o",
        help="Destination graph JSON path (default: ./output/graph.json).",
    ),
    bucket: str | None = typer.Option(
        None,
        "--bucket",
        help="GCS bucket name (defaults to GCS_BUCKET from env).",
    ),
    project_id: str | None = typer.Option(
        None,
        "--project-id",
        help="GCP project id (defaults to GCP_PROJECT_ID from env).",
    ),
    gcs_prefix: str = typer.Option(
        DEFAULT_GCS_PREFIX,
        "--gcs-prefix",
        help="Base GCS prefix used for dataset uploads.",
    ),
    skip_upload: bool = typer.Option(
        False,
        "--skip-upload",
        help="Skip upload and extract directly from an existing GCS prefix.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="Optional LLM model override for table extraction.",
    ),
) -> None:
    """Upload a dataset to GCS and run LLM extraction directly from GCS CSV files."""
    # Lazy import keeps startup fast unless command is used.
    from engine.extractors.table_extractor import (  # noqa: PLC0415
        extract_from_tables_gcs,
    )

    load_env_config()
    resolved_bucket = bucket or os.environ.get("GCS_BUCKET")
    resolved_project = project_id or os.environ.get("GCP_PROJECT_ID")
    if not resolved_bucket:
        typer.echo("Error: missing GCS_BUCKET. Set env or pass --bucket.", err=True)
        raise typer.Exit(code=1)
    if not skip_upload and not resolved_project:
        typer.echo(
            "Error: missing GCP_PROJECT_ID. Set env or pass --project-id.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        source = _resolve_dataset_folder(dataset_name, input_root)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    prefix_base = gcs_prefix.strip("/")
    dataset_prefix = f"{prefix_base}/{source.name}" if prefix_base else source.name

    if not skip_upload:
        typer.echo(f"Uploading {source} to gs://{resolved_bucket}/{prefix_base}/ ...")
        try:
            uploaded = upload_dataset_to_gcs(
                source,
                project_id=resolved_project or "",
                bucket_name=resolved_bucket,
                prefix=prefix_base,
            )
            typer.echo(f"Uploaded {uploaded} file(s) to gs://{resolved_bucket}/{dataset_prefix}")
        except Exception as exc:
            typer.echo(f"Upload failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc

    typer.echo(f"Extracting from gs://{resolved_bucket}/{dataset_prefix} via LLM...")
    try:
        extraction = extract_from_tables_gcs(
            bucket_name=resolved_bucket,
            prefix=dataset_prefix,
            model=model,
            project_id=resolved_project,
        )
    except (EnvironmentError, RuntimeError, ValueError) as exc:
        typer.echo(f"Extraction failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    out_path = _resolve_graph_output_path(source, output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")

    graph = build_graph_from_extraction(extraction)
    graph_path = out_path.with_name("graph.png")
    saved_graph_path = visualize_graph(
        graph,
        str(graph_path),
        title=f"{_dataset_name(source).replace('-', ' ').title()} Graph",
    )

    typer.echo("Extraction complete:")
    typer.echo(f"  - JSON: {out_path.resolve()}")
    typer.echo(f"  - PNG:  {saved_graph_path}")
    typer.echo(f"  - Entities: {len(extraction.get('entities', []))}")
    typer.echo(f"  - Relationships: {len(extraction.get('relationships', []))}")
