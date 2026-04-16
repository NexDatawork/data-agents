"""Tests for GCS-backed table extraction CLI flow."""

import json
from pathlib import Path

from click.testing import CliRunner
from typer.main import get_command

from cli.__main__ import app as cli_app


runner = CliRunner()


def test_extract_tables_gcs_uploads_and_writes_artifacts(
    monkeypatch, tmp_path: Path
) -> None:
    dataset = tmp_path / "input" / "User-DL" / "Airline+Loyalty+Program"
    dataset.mkdir(parents=True)
    (dataset / "sample.csv").write_text("id,name\n1,Alice\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_upload(source: Path, *, project_id: str, bucket_name: str, prefix: str) -> int:
        captured["source"] = source
        captured["project_id"] = project_id
        captured["bucket_name"] = bucket_name
        captured["prefix"] = prefix
        return 1

    def fake_extract_from_tables_gcs(
        *,
        bucket_name: str,
        prefix: str,
        max_rows_per_table: int = 10,
        model: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        del max_rows_per_table
        captured["extract_bucket"] = bucket_name
        captured["extract_prefix"] = prefix
        captured["extract_project"] = project_id
        captured["model"] = model
        return {
            "entities": [{"id": "n1", "label": "Alice", "type": "person"}],
            "relationships": [],
        }

    def fake_visualize(graph, output_path: str, *, title: str | None = None):
        del graph, title
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"png")
        return out.resolve()

    monkeypatch.setattr("cli.commands.extract.upload_dataset_to_gcs", fake_upload)
    monkeypatch.setattr(
        "engine.extractors.table_extractor.extract_from_tables_gcs",
        fake_extract_from_tables_gcs,
    )
    monkeypatch.setattr("cli.commands.extract.visualize_graph", fake_visualize)

    output = tmp_path / "output" / "graph.json"
    result = runner.invoke(
        get_command(cli_app),
        [
            "extract",
            "tables-gcs",
            "Airline+Loyalty+Program",
            "--input-root",
            str(tmp_path / "input"),
            "--output",
            str(output),
        ],
        env={"GCS_BUCKET": "bucket", "GCP_PROJECT_ID": "proj"},
    )

    assert result.exit_code == 0, result.stdout
    assert output.exists()
    assert (output.parent / "graph.png").exists()

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["entities"][0]["id"] == "n1"

    assert captured["source"] == dataset
    assert captured["project_id"] == "proj"
    assert captured["bucket_name"] == "bucket"
    assert captured["prefix"] == "opengraph-ai/input"
    assert captured["extract_bucket"] == "bucket"
    assert captured["extract_prefix"] == "opengraph-ai/input/Airline+Loyalty+Program"


def test_extract_tables_gcs_requires_project_when_uploading(
    monkeypatch, tmp_path: Path
) -> None:
    dataset = tmp_path / "input" / "Airline+Loyalty+Program"
    dataset.mkdir(parents=True)

    # Avoid loading local workspace .env files during this validation test.
    monkeypatch.setattr("cli.commands.extract.load_env_config", lambda: None)
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    result = runner.invoke(
        get_command(cli_app),
        [
            "extract",
            "tables-gcs",
            "Airline+Loyalty+Program",
            "--input-root",
            str(tmp_path / "input"),
        ],
        env={"GCS_BUCKET": "bucket"},
    )

    assert result.exit_code == 1
    assert "missing GCP_PROJECT_ID" in (result.stdout + result.stderr)
