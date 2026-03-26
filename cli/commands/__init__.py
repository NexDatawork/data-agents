"""CLI command registry.

TODO: Split command handlers into dedicated modules.
"""


def list_commands() -> list[str]:
    """Return command names currently implemented.

    TODO: Load commands dynamically from plugins.
    """
    return ["version"]
