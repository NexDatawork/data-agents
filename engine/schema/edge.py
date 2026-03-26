"""Edge schema definitions for graph relationships.

TODO: Add constraints for relation types and directionality.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class Edge:
    """Represent a directed relationship between two nodes.

    TODO: Include confidence scores and provenance.
    """

    source: str
    target: str
    relation: str
    properties: dict[str, str] = field(default_factory=dict)
