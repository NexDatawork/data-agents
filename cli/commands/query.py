"""Query command for the OpenGraph AI CLI.

Builds an offline graph from text/table input and queries it by term.
"""

from pathlib import Path

import typer

from engine.extractors.table_extractor import extract_from_tables_offline
from engine.extractors.text_extractor import extract_from_text_offline
from engine.graphs.builder import build_graph_from_extraction
from engine.graphs.query import query_graph


def query(
    file_path: str = typer.Argument(
        ...,
        help="Path to a text file, or a folder containing CSV tables.",
    ),
    term: str = typer.Argument(
        ...,
        help="Search term, e.g. 'alice'.",
    ),
    exact: bool = typer.Option(
        False,
        "--exact",
        help="Match term exactly against node label or id.",
    ),
) -> None:
    """Query graph nodes and print matches, neighbors, and relations."""
    source = Path(file_path)
    if not source.exists():
        typer.echo(f"Error: file not found — {file_path}", err=True)
        raise typer.Exit(code=1)

    if source.is_dir():
        typer.echo(f"Reading table folder {source} ...")
        try:
            extraction = extract_from_tables_offline(str(source))
        except ValueError as exc:
            typer.echo(f"Extraction failed: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    else:
        typer.echo(f"Reading {source} ...")
        text = source.read_text(encoding="utf-8")
        extraction = extract_from_text_offline(text)

    graph = build_graph_from_extraction(extraction)
    results = query_graph(graph, term=term, exact=exact)

    if not results:
        typer.echo(f"No matches found for '{term}'.")
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(results)} match(es) for '{term}':")
    for item in results:
        typer.echo(f"\n[{item['id']}]  {item['label']}  <{item['type'] or '?'}>")

        neighbors = item["neighbors"]
        if neighbors:
            typer.echo("  Neighbors:")
            for nbr in neighbors:
                typer.echo(f"    - {nbr['id']} ({nbr['label']})")
        else:
            typer.echo("  Neighbors: (none)")

        relations = item["relations"]
        if relations:
            typer.echo("  Relations:")
            for line in relations:
                typer.echo(f"    - {line}")
        else:
            typer.echo("  Relations: (none)")
