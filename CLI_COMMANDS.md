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

Runs the offline pipeline:
- reads text file or table folder
- extracts entities and relationships
- builds the graph
- prints nodes, edges, and graph JSON
- saves graph JSON to `output/<dataset_name>/graph.json` by default

### Text example

```bash
python -m cli demo examples/text_example.txt
```

### Table example

```bash
python -m cli demo examples/table_example
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

Builds a graph and saves it as a PNG image.

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

---

## Current example files

### Text
- [examples/text_example.txt](examples/text_example.txt)

### Tables
- [examples/table_example](examples/table_example)

---

## Notes

- Use the folder [examples/table_example](examples/table_example) for table workflows, not [examples/table_example.csv](examples/table_example.csv).
- `demo`, `query`, and `visualize` currently use the offline extractors.
- `query` reads saved graph JSON from `output/<dataset_name>/graph.json` by default.
- If needed, use `query --rebuild` to regenerate graph JSON from source files.
- `extract text` uses the LLM-backed extractor.
- `visualize --schema-view` is best for understanding the dataset at a high level.
