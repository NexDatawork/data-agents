# OpenGraph AI

<div align="center">

[![Pull Requests](https://img.shields.io/badge/pull%20requests-welcome-5A2AB8?labelColor=3834B6)](https://github.com/your-org/opengraph-ai/pulls)
[![License](https://img.shields.io/badge/license-MIT-5A2AB8?labelColor=3834B6)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-5A2AB8?labelColor=3834B6)](pyproject.toml)
[![Node](https://img.shields.io/badge/node-20%2B-5A2AB8?labelColor=3834B6)](mcp-server/package.json)
[![FastAPI](https://img.shields.io/badge/api-FastAPI-5A2AB8?labelColor=3834B6)](api/main.py)

</div>

OpenGraph AI is a developer toolchain for building agent-first systems over heterogeneous data.

It turns tables, text, images, audio, and video into semantic knowledge graphs for retrieval and reasoning, enabling structured understanding that AI agents can actually use.

## Why It Exists

AI agents struggle with multi-source, unstructured data. Data is often fragmented across files, formats, and modalities, which makes reasoning brittle and context incomplete.

OpenGraph AI adds a graph layer between raw data and agent workflows so entities, relationships, and evidence become explicit and queryable.

## Features (Initial Version)

- Extract graph structures from text
- Extract graph structures from tables
- Convert entities and relationships into graph JSON
- Query the graph
- Run graph workflows from CLI commands
- Access graph workflows through API endpoints
- Expose graph tooling to agent runtimes via MCP tools

## Project Components

- Python CLI (Typer-oriented command layer)
- Python API service (FastAPI)
- Node.js MCP server (Claude Code and Cursor integration)
- Shared Python engine for extraction, graph build, and query operations

## Installation

### 1. Install CLI via pip

```bash
pip install -e .
python -m cli --version
```

### 2. Run API server

```bash
pip install -e .
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Use MCP server with Claude Code or Cursor

```bash
cd mcp-server
npm install
npm run dev
```

Then register the MCP server command in your Claude Code or Cursor MCP configuration.

## Quickstart Examples

### Text Extraction

```python
from engine.extractors.text_extractor import extract_text

chunks = extract_text("Alice founded Acme Corp in 2020.\nAcme acquired Beta Labs.")
print(chunks)
```

### Table Extraction

```python
from engine.extractors.table_extractor import extract_table

rows = extract_table("examples/table_example.csv")
print(rows[:2])
```

### Graph Query

```python
from engine.graphs.builder import build_graph
from engine.graphs.query import get_node

records = [
    {"id": "entity-1", "label": "Alice", "type": "person"},
    {"id": "entity-2", "label": "Acme", "type": "company"},
]

graph = build_graph(records)
print(get_node(graph, "entity-1"))
```

## Architecture Overview

```text
CLI (Python) --------------> Shared Engine (Python)
API (FastAPI) -------------> Shared Engine (Python)
MCP (Node.js) -> Python wrapper -> Shared Engine (Python)
```

Core flow:
- Extract modality-specific data
- Normalize entities and relationships
- Build graph JSON
- Query for retrieval and reasoning

## Roadmap

- Add extraction support for images
- Add extraction support for audio
- Add extraction support for video
- Add vector database connectors
- Add higher-level agent workflow orchestration

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome.

- Open an issue with problem statement and reproducible context
- Propose design updates via pull request
- Include tests for new extraction, graph, or query behavior
- Keep public APIs typed and documented

Initial contribution guidance is available at [archive/CONTRIBUTING.md](archive/CONTRIBUTING.md).