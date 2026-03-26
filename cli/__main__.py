"""CLI entrypoint for OpenGraph AI.

Mounts subcommand groups onto the root Typer application.
Run with:  python -m cli [OPTIONS] COMMAND [ARGS]...
"""

import typer

from cli.commands.demo import demo
from cli.commands.extract import app as extract_app

app = typer.Typer(
    name="opengraph",
    help="OpenGraph AI — turn heterogeneous data into semantic knowledge graphs.",
    no_args_is_help=True,
)

# ── Register subcommand groups ────────────────────────────────────────────────
app.add_typer(extract_app, name="extract")

# ── Register direct commands ──────────────────────────────────────────────────
app.command("demo")(demo)


@app.callback(invoke_without_command=True)
def root(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
) -> None:
    """OpenGraph AI CLI root command."""
    if version:
        typer.echo("opengraph 0.1.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()
