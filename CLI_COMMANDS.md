# OpenGraph AI CLI Commands

This file lists the current CLI commands and ready-to-run examples for local testing.

## Prerequisites

Install the project in editable mode:

```bash
pip install -e .
```

You can then use either form:

```bash
python -m cli ...
```

or:

```bash
opengraph ...
```

---

## 1. Check CLI version

```bash
python -m cli --version
```

---

## 2. `demo`

Runs the pipeline:
- reads text file or table folder
- extracts entities and relationships
- builds the graph
- prints nodes, edges, and graph JSON
- saves graph JSON to `output/<dataset_name>/graph.json` by default

For table folders, you can choose:
- default offline mode
- `--llm` for LLM-backed extraction

### Text example

```bash
python -m cli demo examples/text_example.txt
```

### Table example

```bash
python -m cli demo examples/table_example
```

### Table example with LLM mode

> Requires `OPENAI_API_KEY` to be set.

```bash
python -m cli demo examples/table_example --llm
```

Default saved file:

```text
output/table_example/graph.json
```

---

## 3. `query`

Loads saved graph JSON from `output/<dataset_name>/graph.json` and searches for matching nodes.

Output includes:
- matching node
- neighbors
- relations

### Text example: query Alice

```bash
python -m cli query examples/text_example.txt alice
```

### Text example: exact match

```bash
python -m cli query examples/text_example.txt "Alice Johnson" --exact
```

### Table example: broad customer query

```bash
python -m cli query examples/table_example customer
```

This reads from:

```text
output/table_example/graph.json
```

### Table example: exact node lookup

```bash
python -m cli query examples/table_example "customers:c003" --exact
```

### Table example: exact order lookup

```bash
python -m cli query examples/table_example "orders:o1003" --exact
```

### Rebuild graph before querying

```bash
python -m cli query examples/table_example customer --rebuild
```

---

## 4. `visualize`

Loads saved graph JSON from `output/<dataset_name>/graph.json` by default and saves it as a PNG image.

Use `--rebuild` only if you want to regenerate the graph from the source files.

If `--output` points directly under `output/`, the CLI automatically creates a dataset-named subfolder:
- table folder input `examples/table_example` → `output/table_example/...`
- text file input `examples/text_example.txt` → `output/text_example/...`

### Text example graph image

```bash
python -m cli visualize examples/text_example.txt --output output/text-example-graph.png --title "Text Example Graph"
```

### Table example full graph image

```bash
python -m cli visualize examples/table_example --output output/table-example-graph.png --title "Table Example Graph"
```

Result path:

```text
output/table_example/table-example-graph.png
```

### Table example schema view

This is the cleaner, human-friendly overview.

```bash
python -m cli visualize examples/table_example --schema-view --output output/table-example-schema.png --title "Table Example Schema"
```

### Rebuild before visualizing

```bash
python -m cli visualize examples/table_example --schema-view --rebuild --output output/table-example-schema.png
```

### Text example schema view

```bash
python -m cli visualize examples/text_example.txt --schema-view --output output/text-example-schema.png --title "Text Example Schema"
```

---

## 5. `extract text`

Runs the LLM-backed text extractor and writes graph JSON to disk.

> Requires `OPENAI_API_KEY` to be set.

### Text extraction example

```bash
python -m cli extract text examples/text_example.txt --output output/text-graph.json
```

### Table dataset via GCS (upload then extract)

This flow is useful for Cloud Run preparation: upload local dataset folder into
GCS, then run LLM extraction by reading CSV files from GCS.

```bash
python -m cli extract tables-gcs "Airline+Loyalty+Program"
```

Optional flags:
- `--input-root ./input`
- `--bucket <bucket-name>`
- `--project-id <gcp-project-id>`
- `--gcs-prefix opengraph-ai/input`
- `--skip-upload` (extract from already uploaded files)
- `--model gpt-4o-mini`

---

## 6. `upload`

Uploads a dataset folder from the `input/` tree to Google Cloud Storage.

The command takes the dataset folder name, not the full path. It searches under
`input/` recursively, so a folder like `input/User-DL/Airline+Loyalty+Program`
can be uploaded by passing only `Airline+Loyalty+Program`.

> Requires `GCP_PROJECT_ID`, `GCS_BUCKET`, and valid Google credentials.

### Airline dataset upload

```bash
python -m cli upload "Airline+Loyalty+Program"
```

### Override bucket prefix

```bash
python -m cli upload "Airline+Loyalty+Program" --prefix opengraph-ai/datasets
```

---

## 7. `graphdb` (Neo4j AuraDB)

Use this when you want to store extracted nodes/edges in Neo4j AuraDB, then
export them back to graph JSON later.

Required env vars:

```dotenv
NEO4J_URI=neo4j+s://<your-aura-host>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>
# Optional (default: neo4j)
NEO4J_DATABASE=neo4j
```

### Push graph JSON to Neo4j

```bash
python -m cli graphdb push output/Airline-Loyalty-Program/graph.json --dataset Airline-Loyalty-Program
```

### Pull graph JSON back from Neo4j

```bash
python -m cli graphdb pull Airline-Loyalty-Program --output output/graph.json
```

### End-to-end from GCS → LLM → Neo4j → GCS artifacts

Use this after dataset files are in the bucket. The command:
1) reads CSV dataset from GCS,
2) runs LLM extraction,
3) stores nodes/edges in Neo4j,
4) exports Neo4j graph JSON + renders PNG,
5) uploads JSON + PNG back to GCS,
6) prints final JSON in CLI output.

```bash
python -m cli graphdb from-gcs "Airline+Loyalty+Program"
```

This command now writes both artifacts and prints them in CLI output:
- graph JSON
- graph PNG (`graph.png` by default in the same folder)
- entity/relationship counts

This writes to:

```text
output/Airline-Loyalty-Program/graph.json
```

---

## Recommended test sequence

If you want to quickly verify the current CLI end to end, run these in order.

### A. Text flow

```bash
python -m cli demo examples/text_example.txt
python -m cli query examples/text_example.txt alice
python -m cli visualize examples/text_example.txt --output output/text-example-graph.png --title "Text Example Graph"
```

### B. Table flow

```bash
python -m cli demo examples/table_example
python -m cli query examples/table_example customer
python -m cli query examples/table_example "customers:c003" --exact
python -m cli visualize examples/table_example --output output/table-example-graph.png --title "Table Example Graph"
python -m cli visualize examples/table_example --schema-view --output output/table-example-schema.png --title "Table Example Schema"
```

### C. Airline dataset end-to-end with LLM

Start from the project root:

```bash
cd /Users/d/Documents/GitHub/opengraph-ai
source .venv/bin/activate
```

If your `.env.local` already has `OPENAI_API_KEY`, `GCS_BUCKET`,
`GCP_PROJECT_ID`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`,
and `NEO4J_DATABASE`, you can run the cloud workflow directly.

Upload dataset folder from `input/` to GCS:

```bash
python -m cli upload "Airline+Loyalty+Program"
```

Build graph from GCS (LLM extraction), store in Neo4j, export JSON+PNG,
upload artifacts back to GCS, and print final JSON in CLI:

```bash
python -m cli graphdb from-gcs "Airline+Loyalty+Program" --output output/airline-from-gcs-neo4j.json --model gpt-4o-mini
```

Run the dataset through LLM extraction and save graph JSON:

```bash
python -m cli demo "input/User-DL/Airline+Loyalty+Program" --llm
```

That saves to:

```text
output/Airline-Loyalty-Program/graph.json
```

Query the saved graph:

```bash
python -m cli query "input/User-DL/Airline+Loyalty+Program" loyalty
```

Render the saved graph as a schema image:

```bash
python -m cli visualize "input/User-DL/Airline+Loyalty+Program" --schema-view --output output/airline_schema.png
```

Render the saved graph as a full graph image:

```bash
python -m cli visualize "input/User-DL/Airline+Loyalty+Program" --output output/airline_graph.png
```

---

## Current example files

### Text
- [examples/text_example.txt](examples/text_example.txt)

### Tables
- [examples/table_example](examples/table_example)

---

## Notes

- Use the folder [examples/table_example](examples/table_example) for table workflows, not [examples/table_example.csv](examples/table_example.csv).
- `demo` uses offline extraction by default, and supports LLM table extraction with `--llm`.
- `query` reads saved graph JSON from `output/<dataset_name>/graph.json` by default.
- If needed, use `query --rebuild` to regenerate graph JSON from source files.
- `visualize` now reads saved graph JSON by default.
- If needed, use `visualize --rebuild` to regenerate graph JSON from source files before rendering.
- `extract text` uses the LLM-backed extractor.
- `upload` resolves dataset folders by name from inside `input/`.
- `graphdb push` stores entities/relationships into Neo4j AuraDB.
- `graphdb pull` exports Neo4j nodes/edges back into `graph.json` format.
- `visualize --schema-view` is best for understanding the dataset at a high level.
