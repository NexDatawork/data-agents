"""Node schema definitions for graph entities.

TODO: Add richer metadata and validation rules.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class Node:
    """Represent a node in the graph.

    TODO: Introduce typed property models.
    """

    id: str
    label: str
    properties: dict[str, str] = field(default_factory=dict)
