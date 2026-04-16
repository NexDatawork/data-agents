"""End-to-end workflow for GCS dataset → LLM extraction → Neo4j → GCS artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from engine.config import load_env_config
from engine.connectors.neo4j_aura import export_extraction_from_neo4j
from engine.connectors.neo4j_aura import store_extraction_in_neo4j
from engine.extractors.table_extractor import extract_from_tables_gcs
from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.visualize import visualize_graph
from engine.graphs.visualize import visualize_schema_graph
from engine.upload.gcp import DEFAULT_GCS_PREFIX
from engine.upload.gcp import upload_file_to_gcs

DEFAULT_GCS_OUTPUT_PREFIX = "opengraph-ai/output"


def resolve_output_json_path(dataset: str, output: str) -> Path:
    """Resolve JSON output path with dataset subfolder defaults."""
    out_path = Path(output)
    if out_path.suffix == "":
        return out_path / dataset / "graph.json"
    if out_path.parent == Path("output"):
        return out_path.parent / dataset / out_path.name
    return out_path


def run_graph_from_gcs_workflow(
    *,
    dataset: str,
    bucket: str | None = None,
    input_prefix: str = DEFAULT_GCS_PREFIX,
    output_prefix: str = DEFAULT_GCS_OUTPUT_PREFIX,
    output: str = "./output/graph.json",
    model: str | None = None,
    project_id: str | None = None,
    schema_view: bool = False,
) -> dict[str, Any]:
    """Run the complete graph workflow and return summary plus graph JSON payload."""
    load_env_config()

    resolved_bucket = bucket or os.environ.get("GCS_BUCKET")
    resolved_project = project_id or os.environ.get("GCP_PROJECT_ID")
    if not resolved_bucket:
        raise EnvironmentError("GCS_BUCKET is not set. Pass bucket or set it in the environment.")

    clean_input = input_prefix.strip("/")
    dataset_input_prefix = f"{clean_input}/{dataset}" if clean_input else dataset

    extraction = extract_from_tables_gcs(
        bucket_name=resolved_bucket,
        prefix=dataset_input_prefix,
        model=model,
        project_id=resolved_project,
    )

    stored_counts = store_extraction_in_neo4j(
        extraction,
        dataset=dataset,
        clear_existing=True,
    )

    neo4j_payload = export_extraction_from_neo4j(dataset=dataset)

    out_path = resolve_output_json_path(dataset, output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(neo4j_payload, indent=2), encoding="utf-8")

    graph_path = out_path.with_name("graph.png")
    graph = build_graph_from_extraction(neo4j_payload)
    renderer = visualize_schema_graph if schema_view else visualize_graph
    saved_graph_path = renderer(
        graph,
        str(graph_path),
        title=f"{dataset.replace('-', ' ').replace('+', ' ').title()} Graph",
    )

    clean_output = output_prefix.strip("/")
    json_blob_name = (
        f"{clean_output}/{dataset}/{out_path.name}" if clean_output else f"{dataset}/{out_path.name}"
    )
    png_blob_name = (
        f"{clean_output}/{dataset}/{saved_graph_path.name}"
        if clean_output
        else f"{dataset}/{saved_graph_path.name}"
    )

    json_gcs_uri = upload_file_to_gcs(
        out_path,
        bucket_name=resolved_bucket,
        blob_name=json_blob_name,
        project_id=resolved_project,
    )
    png_gcs_uri = upload_file_to_gcs(
        saved_graph_path,
        bucket_name=resolved_bucket,
        blob_name=png_blob_name,
        project_id=resolved_project,
    )

    entity_count = len(neo4j_payload.get("entities", []))
    relationship_count = len(neo4j_payload.get("relationships", []))

    return {
        "dataset": dataset,
        "gcs_input_uri": f"gs://{resolved_bucket}/{dataset_input_prefix}",
        "gcs_json_uri": json_gcs_uri,
        "gcs_png_uri": png_gcs_uri,
        "local_json_path": str(out_path.resolve()),
        "local_png_path": str(saved_graph_path),
        "stored_node_count": stored_counts["node_count"],
        "stored_edge_count": stored_counts["edge_count"],
        "entity_count": entity_count,
        "relationship_count": relationship_count,
        "graph_json": neo4j_payload,
    }