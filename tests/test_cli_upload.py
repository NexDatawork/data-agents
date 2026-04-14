"""Tests for the upload CLI command."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.__main__ import app
from cli.commands.upload import _resolve_dataset_folder


def test_resolve_dataset_folder_finds_recursive_match(tmp_path: Path) -> None:
    dataset = tmp_path / "input" / "User-DL" / "Airline+Loyalty+Program"
    dataset.mkdir(parents=True)

    resolved = _resolve_dataset_folder("Airline+Loyalty+Program", str(tmp_path / "input"))

    assert resolved == dataset


def test_resolve_dataset_folder_rejects_duplicates(tmp_path: Path) -> None:
    (tmp_path / "input" / "a" / "dup").mkdir(parents=True)
    (tmp_path / "input" / "b" / "dup").mkdir(parents=True)

    with pytest.raises(ValueError):
        _resolve_dataset_folder("dup", str(tmp_path / "input"))


def test_upload_command_uses_dataset_name_from_input_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = tmp_path / "input" / "User-DL" / "Airline+Loyalty+Program"
    dataset.mkdir(parents=True)
    (dataset / "customers.csv").write_text("id\n1\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_upload(source: Path, *, project_id: str, bucket_name: str, prefix: str) -> int:
        captured["source"] = source
        captured["project_id"] = project_id
        captured["bucket_name"] = bucket_name
        captured["prefix"] = prefix
        return 1

    monkeypatch.setattr("cli.commands.upload.upload_dataset_to_gcs", fake_upload)
    monkeypatch.setattr("cli.commands.upload.load_local_env", lambda: None)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "upload",
            "Airline+Loyalty+Program",
            "--input-root",
            str(tmp_path / "input"),
        ],
        env={"GCP_PROJECT_ID": "proj", "GCS_BUCKET": "bucket"},
    )

    assert result.exit_code == 0
    assert captured == {
        "source": dataset,
        "project_id": "proj",
        "bucket_name": "bucket",
        "prefix": "opengraph-ai/input",
    }
    assert "Uploading dataset folder 'Airline+Loyalty+Program'" in result.stdout