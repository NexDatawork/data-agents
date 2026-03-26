"""API route definitions.

TODO: Add route modules for extract, graph, and query endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return health status.

    TODO: Add deep dependency readiness checks.
    """
    return {"status": "ok"}
