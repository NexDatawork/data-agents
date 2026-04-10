"""Tests for the LLM-backed text extraction pipeline."""

import json
from pathlib import Path

from click.testing import CliRunner
from typer.main import get_command

from cli.__main__ import app as cli_app
from engine.extractors.text_extractor import (
    extract_from_text,
    load_text_source,
    write_extraction_artifacts,
)


runner = CliRunner()


def test_extract_from_text_chunks_long_input(monkeypatch) -> None:
    prompts: list[str] = []

    def fake_call_llm(prompt: str, **_: object) -> str:
        prompts.append(prompt)
        if len(prompts) == 1:
            return json.dumps(
                {
                    "entities": [{"id": "alice", "label": "Alice", "type": "person"}],
                    "relationships": [],
                }
            )
        return json.dumps(
            {
                "entities": [{"id": "acme", "label": "Acme", "type": "org"}],
                "relationships": [
                    {"source": "alice", "target": "acme", "relation": "founded"}
                ],
            }
        )

    monkeypatch.setattr("engine.extractors.text_extractor.call_llm", fake_call_llm)

    text = ("Alice founded Acme Corporation in London.\n" * 30).strip()
    result = extract_from_text(text, max_chunk_chars=120)

    assert len(prompts) > 1
    assert {entity["id"] for entity in result["entities"]} >= {"alice", "acme"}
    assert result["metadata"]["chunk_count"] == len(prompts)
    assert result["metadata"]["input_characters"] == len(text)


def test_load_text_source_supports_pdf(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "uploads" / "demo.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(b"%PDF-1.4\n%demo\n")

    class FakePage:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class FakePdfReader:
        def __init__(self, source: Path) -> None:
            assert Path(source) == pdf_path
            self.pages = [
                FakePage("Alice founded Acme Corporation."),
                FakePage("Acme acquired Beta Labs."),
            ]

    monkeypatch.setattr("engine.extractors.text_extractor.PdfReader", FakePdfReader)

    text, metadata = load_text_source(pdf_path)

    assert "Alice founded Acme Corporation." in text
    assert "Acme acquired Beta Labs." in text
    assert metadata["source_type"] == "pdf"
    assert metadata["source_name"] == "demo"


def test_write_extraction_artifacts_persists_json_and_graph(tmp_path: Path) -> None:
    extraction = {
        "entities": [
            {"id": "alice", "label": "Alice", "type": "person"},
            {"id": "acme", "label": "Acme", "type": "org"},
        ],
        "relationships": [
            {"source": "alice", "target": "acme", "relation": "founded"},
        ],
        "metadata": {"source_type": "text", "source_name": "demo"},
    }

    output_path = tmp_path / "output" / "graph.json"
    artifacts = write_extraction_artifacts(
        extraction,
        source=tmp_path / "examples" / "demo.txt",
        output_path=output_path,
        title="Demo Graph",
    )

    assert artifacts["json_path"] == output_path.resolve()
    assert artifacts["graph_path"].exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["source_name"] == "demo"
    assert payload["entities"][0]["label"] == "Alice"


def test_extract_cli_writes_json_and_graph(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "examples" / "demo.txt"
    source.parent.mkdir(parents=True)
    source.write_text("Alice founded Acme Corporation.", encoding="utf-8")

    def fake_call_llm(prompt: str, **_: object) -> str:
        assert "Alice founded Acme Corporation." in prompt
        return json.dumps(
            {
                "entities": [
                    {"id": "alice", "label": "Alice", "type": "person"},
                    {"id": "acme", "label": "Acme Corporation", "type": "org"},
                ],
                "relationships": [
                    {"source": "alice", "target": "acme", "relation": "founded"},
                ],
            }
        )

    monkeypatch.setattr("engine.extractors.text_extractor.call_llm", fake_call_llm)

    output_path = tmp_path / "output" / "graph.json"
    result = runner.invoke(
        get_command(cli_app),
        ["extract", "text", str(source), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.stdout
    assert output_path.exists()
    assert (output_path.parent / "graph.png").exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["source_name"] == "demo"
