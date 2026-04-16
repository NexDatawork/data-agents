"""Graph database subcommands for Neo4j AuraDB integration."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer

from engine.connectors.neo4j_aura import export_extraction_from_neo4j
from engine.connectors.neo4j_aura import store_extraction_in_neo4j
from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.visualize import visualize_graph
from engine.graphs.visualize import visualize_schema_graph
from engine.upload.gcp import DEFAULT_GCS_PREFIX
from engine.workflows.graph_from_gcs import DEFAULT_GCS_OUTPUT_PREFIX
from engine.workflows.graph_from_gcs import resolve_output_json_path
from engine.workflows.graph_from_gcs import run_graph_from_gcs_workflow

app = typer.Typer(help="Store and retrieve extraction graphs from Neo4j AuraDB.")


def _dataset_name_from_json_path(path: Path) -> str:
    """Derive a stable dataset key from a graph JSON path."""
    base = path.parent.name if path.name == "graph.json" else path.stem
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", base).strip("-._")
    return normalized or "dataset"


@app.command("push")
def push(
    graph_json: str = typer.Argument(
        ..., help="Path to extraction graph JSON with entities/relationships keys."
    ),
    dataset: str | None = typer.Option(
        None,
        "--dataset",
        help="Dataset namespace in Neo4j (default derived from graph_json path).",
    ),
    clear_existing: bool = typer.Option(
        True,
        "--clear-existing/--append",
        help="Clear existing records for this dataset before upload (default: clear).",
    ),
) -> None:
    """Push extraction JSON nodes/edges into Neo4j AuraDB."""
    graph_path = Path(graph_json)
    if not graph_path.exists() or not graph_path.is_file():
        typer.echo(f"Error: graph JSON file not found: {graph_json}", err=True)
        raise typer.Exit(code=1)

    try:
        extraction = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: invalid JSON file: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not isinstance(extraction, dict):
        typer.echo("Error: extraction payload must be a JSON object.", err=True)
        raise typer.Exit(code=1)
    if "entities" not in extraction or "relationships" not in extraction:
        typer.echo(
            "Error: extraction payload must include 'entities' and 'relationships'.",
            err=True,
        )
        raise typer.Exit(code=1)

    dataset_name = dataset or _dataset_name_from_json_path(graph_path)

    try:
        counts = store_extraction_in_neo4j(
            extraction,
            dataset=dataset_name,
            clear_existing=clear_existing,
        )
    except (EnvironmentError, RuntimeError, ValueError) as exc:
        typer.echo(f"Upload to Neo4j failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Stored dataset '{dataset_name}' in Neo4j with {counts['node_count']} node(s) and {counts['edge_count']} edge(s)."
    )


@app.command("pull")
def pull(
    dataset: str = typer.Argument(..., help="Dataset namespace to export from Neo4j."),
    output: str = typer.Option(
        "./output/graph.json",
        "--output",
        "-o",
        help="Destination file for exported graph JSON.",
    ),
    graph_output: str | None = typer.Option(
        None,
        "--graph-output",
        help="Destination PNG path for rendered graph (default: <json_dir>/graph.png).",
    ),
    schema_view: bool = typer.Option(
        False,
        "--schema-view",
        help="Render schema/entity-type graph view instead of full row-level graph.",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="Optional graph title for rendered PNG.",
    ),
) -> None:
    """Pull a dataset from Neo4j AuraDB into extraction JSON format."""
    out_path = resolve_output_json_path(dataset, output)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        extraction = export_extraction_from_neo4j(dataset=dataset)
    except (EnvironmentError, RuntimeError, ValueError) as exc:
        typer.echo(f"Export from Neo4j failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    out_path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")

    graph_path = Path(graph_output) if graph_output else out_path.with_name("graph.png")
    graph_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        graph = build_graph_from_extraction(extraction)
        renderer = visualize_schema_graph if schema_view else visualize_graph
        saved_graph_path = renderer(
            graph,
            str(graph_path),
            title=title or f"{dataset.replace('-', ' ').title()} Graph",
        )
    except ValueError as exc:
        typer.echo(f"Graph render failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    entity_count = len(extraction.get("entities", []))
    relationship_count = len(extraction.get("relationships", []))
    typer.echo(f"Exported dataset '{dataset}' from Neo4j")
    typer.echo(f"  - JSON: {out_path.resolve()}")
    typer.echo(f"  - PNG:  {saved_graph_path}")
    typer.echo(f"  - Entities: {entity_count}")
    typer.echo(f"  - Relationships: {relationship_count}")


@app.command("from-gcs")
def from_gcs(
    dataset: str = typer.Argument(..., help="Dataset folder name already uploaded to GCS."),
    bucket: str | None = typer.Option(
        None,
        "--bucket",
        help="GCS bucket name (defaults to GCS_BUCKET from env).",
    ),
    input_prefix: str = typer.Option(
        DEFAULT_GCS_PREFIX,
        "--input-prefix",
        help="Base GCS input prefix containing uploaded dataset folders.",
    ),
    output_prefix: str = typer.Option(
        DEFAULT_GCS_OUTPUT_PREFIX,
        "--output-prefix",
        help="Base GCS output prefix for graph artifacts.",
    ),
    output: str = typer.Option(
        "./output/graph.json",
        "--output",
        "-o",
        help="Local destination file for exported graph JSON.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="Optional LLM model override for extraction.",
    ),
    project_id: str | None = typer.Option(
        None,
        "--project-id",
        help="GCP project id (defaults to GCP_PROJECT_ID from env).",
    ),
    schema_view: bool = typer.Option(
        False,
        "--schema-view",
        help="Render schema/entity-type graph view instead of full row-level graph.",
    ),
    print_json: bool = typer.Option(
        True,
        "--print-json/--no-print-json",
        help="Print final Neo4j-exported graph JSON in CLI output.",
    ),
) -> None:
    """Create graph from GCS dataset via LLM, store in Neo4j, and publish artifacts to GCS."""
    try:
        result = run_graph_from_gcs_workflow(
            dataset=dataset,
            bucket=bucket,
            input_prefix=input_prefix,
            output_prefix=output_prefix,
            output=output,
            model=model,
            project_id=project_id,
            schema_view=schema_view,
        )
    except (EnvironmentError, RuntimeError, ValueError) as exc:
        typer.echo(f"Workflow failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Workflow complete for dataset '{dataset}'")
    typer.echo(f"  - GCS input:  {result['gcs_input_uri']}")
    typer.echo(f"  - Neo4j stored nodes: {result['stored_node_count']}")
    typer.echo(f"  - Neo4j stored edges: {result['stored_edge_count']}")
    typer.echo(f"  - Local JSON: {result['local_json_path']}")
    typer.echo(f"  - Local PNG:  {result['local_png_path']}")
    typer.echo(f"  - GCS JSON:   {result['gcs_json_uri']}")
    typer.echo(f"  - GCS PNG:    {result['gcs_png_uri']}")
    typer.echo(f"  - Entities: {result['entity_count']}")
    typer.echo(f"  - Relationships: {result['relationship_count']}")

    if print_json:
        typer.echo("\nNeo4j graph JSON:")
        typer.echo(json.dumps(result["graph_json"], indent=2))
