"""CLI command registry.

Registers subcommand Typer apps onto the root CLI.
TODO: Load commands dynamically from plugins.
"""

from cli.commands import extract  # noqa: F401
from cli.commands import upload  # noqa: F401


def list_commands() -> list[str]:
    """Return command names currently implemented.

    TODO: Load commands dynamically from plugins.
    """
    return ["version", "extract", "demo", "query", "upload", "visualize"]
