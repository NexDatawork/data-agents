"""API route definitions.

TODO: Add route modules for extract, graph, and query endpoints.
"""

from pydantic import BaseModel
from fastapi import APIRouter
from fastapi import HTTPException

from engine.upload.gcp import DEFAULT_GCS_PREFIX
from engine.workflows.graph_from_gcs import DEFAULT_GCS_OUTPUT_PREFIX
from engine.workflows.graph_from_gcs import run_graph_from_gcs_workflow

router = APIRouter()


class GraphFromGcsRequest(BaseModel):
    """Request body for running the graph workflow from a GCS dataset."""

    dataset: str
    bucket: str | None = None
    input_prefix: str = DEFAULT_GCS_PREFIX
    output_prefix: str = DEFAULT_GCS_OUTPUT_PREFIX
    output: str = "./output/graph.json"
    model: str | None = None
    project_id: str | None = None
    schema_view: bool = False


class GraphFromGcsResponse(BaseModel):
    """Response body for the graph workflow."""

    dataset: str
    gcs_input_uri: str
    gcs_json_uri: str
    gcs_png_uri: str
    local_json_path: str
    local_png_path: str
    stored_node_count: int
    stored_edge_count: int
    entity_count: int
    relationship_count: int
    graph_json: dict


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return health status.

    TODO: Add deep dependency readiness checks.
    """
    return {"status": "ok"}


@router.post("/graph/from-gcs", tags=["graph"], response_model=GraphFromGcsResponse)
def graph_from_gcs(request: GraphFromGcsRequest) -> GraphFromGcsResponse:
    """Run the GCS → LLM → Neo4j → GCS graph workflow for a dataset."""
    try:
        result = run_graph_from_gcs_workflow(
            dataset=request.dataset,
            bucket=request.bucket,
            input_prefix=request.input_prefix,
            output_prefix=request.output_prefix,
            output=request.output,
            model=request.model,
            project_id=request.project_id,
            schema_view=request.schema_view,
        )
    except (EnvironmentError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return GraphFromGcsResponse(**result)
