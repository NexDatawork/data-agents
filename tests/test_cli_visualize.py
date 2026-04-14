"""Tests for visualize CLI path resolution behavior."""

from pathlib import Path

from cli.commands.visualize import _resolve_output_path


def test_resolve_output_path_inserts_dataset_folder_for_output_root() -> None:
    source = Path("examples/table_example")
    resolved = _resolve_output_path(source, "output/table-example-graph.png")
    assert resolved == Path("output/table_example/table-example-graph.png")


def test_resolve_output_path_uses_file_stem_for_text_dataset() -> None:
    source = Path("examples/text_example.txt")
    resolved = _resolve_output_path(source, "output/text-graph.png")
    assert resolved == Path("output/text_example/text-graph.png")


def test_resolve_output_path_preserves_custom_nested_destination() -> None:
    source = Path("examples/table_example")
    resolved = _resolve_output_path(source, "output/custom/table-example-graph.png")
    assert resolved == Path("output/custom/table-example-graph.png")
