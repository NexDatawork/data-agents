"""Connector interfaces for external sources.

TODO: Add concrete connectors for databases and APIs.
"""


def available_connectors() -> list[str]:
    """List currently available connector names.

    TODO: Discover connectors via plugin registration.
    """
    return ["neo4j_aura"]
