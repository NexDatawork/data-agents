"""Table extraction helpers for OpenGraph AI.

Two modes:
- extract_from_tables_offline: deterministic relational inference from CSV tables.
- extract_from_tables: LLM-backed extraction over table snapshots.

This module is tuned for the demo relational dataset in examples/table_example.

TODO: Add schema contracts and stronger type normalization.
"""

import csv
import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def extract_table(path: str) -> list[dict[str, str]]:
    """Extract rows from a single CSV file.

    TODO: Handle malformed files and non-CSV formats.
    """
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def extract_tables(path: str) -> dict[str, list[dict[str, str]]]:
    """Extract all CSV tables from a folder.

    Returns a dictionary keyed by table name (CSV stem).

    Example:
        extract_tables("examples/table_example")
    """
    folder = Path(path)
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Table folder does not exist or is not a directory: {path}")

    # Keep deterministic ordering for stable outputs across runs/tests.
    tables: dict[str, list[dict[str, str]]] = {}
    for csv_file in sorted(folder.glob("*.csv")):
        tables[csv_file.stem] = extract_table(str(csv_file))

    if not tables:
        raise ValueError(f"No CSV tables found in folder: {path}")

    return tables


def _slug(value: str) -> str:
    """Create a stable lowercase slug for entity ids."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _guess_primary_key(table_name: str, rows: list[dict[str, str]]) -> str:
    """Infer primary key column from a table's header.

    Heuristic order:
    1) <singular_table_name>_id
    2) first column ending with _id
    3) first column
    """
    if not rows:
        raise ValueError(f"Cannot infer primary key for empty table: {table_name}")

    columns = list(rows[0].keys())
    singular = table_name[:-1] if table_name.endswith("s") else table_name
    candidate = f"{singular}_id"
    if candidate in columns:
        return candidate

    for col in columns:
        if col.endswith("_id"):
            return col

    return columns[0]


# ---------------------------------------------------------------------------
# Offline extraction (deterministic, no API key required)
# ---------------------------------------------------------------------------

def extract_from_tables_offline(path: str) -> dict:
    """Extract entities and relationships from a folder of CSV tables.

    Returns shape compatible with build_graph_from_extraction:
        {"entities": [...], "relationships": [...]}.

    Relationship inference is heuristic and based on *_id foreign-key naming.

    TODO: Replace heuristics with explicit schema/constraints support.
    """
    tables = extract_tables(path)

    # Infer one primary-key-like column per table so each row gets a stable node id.
    primary_keys: dict[str, str] = {
        table_name: _guess_primary_key(table_name, rows)
        for table_name, rows in tables.items()
    }

    # Index possible reference targets by matching primary-key column name.
    fk_targets: dict[str, str] = {}
    for table_name, pk_col in primary_keys.items():
        fk_targets[pk_col] = table_name

    entities: list[dict] = []
    relationships: list[dict] = []
    seen_entities: set[str] = set()
    seen_relationships: set[tuple[str, str, str]] = set()

    # Walk every table row to emit one entity plus zero or more FK relationships.
    for table_name, rows in tables.items():
        pk_col = primary_keys[table_name]
        # Keep singularization intentionally simple to mirror demo expectations.
        singular = table_name[:-1] if table_name.endswith("s") else table_name

        for row_index, row in enumerate(rows, start=1):
            raw_pk = (row.get(pk_col) or "").strip()
            if raw_pk:
                node_id = f"{table_name}:{_slug(raw_pk)}"
            else:
                node_id = f"{table_name}:row-{row_index}"

            # Prefer *_name columns for human labels; fall back to primary key.
            label_col = next(
                (k for k in row if k.endswith("_name") and row.get(k)),
                pk_col,
            )
            label = row.get(label_col, raw_pk or node_id)

            if node_id not in seen_entities:
                seen_entities.add(node_id)
                entities.append(
                    {
                        "id": node_id,
                        "label": label,
                        "type": singular,
                        "properties": {"table": table_name, **row},
                    }
                )

            # Treat non-primary *_id fields as possible foreign keys.
            for column, value in row.items():
                if column == pk_col or not column.endswith("_id"):
                    continue
                fk_value = (value or "").strip()
                if not fk_value:
                    continue

                target_table = fk_targets.get(column)
                if not target_table:
                    continue

                target_id = f"{target_table}:{_slug(fk_value)}"
                # Convert column name like customer_id -> relation customer.
                relation = column.removesuffix("_id")
                signature = (node_id, target_id, relation)
                if signature in seen_relationships:
                    continue

                seen_relationships.add(signature)
                relationships.append(
                    {
                        "source": node_id,
                        "target": target_id,
                        "relation": relation,
                    }
                )

    return {"entities": entities, "relationships": relationships}


# ---------------------------------------------------------------------------
# LLM-backed extraction (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------

from engine.llm.provider import call_llm  # noqa: E402

_TABLE_EXTRACTION_PROMPT = (
    "You are given relational table snapshots from CSV files.\n"
    "Extract entities and relationships that best represent the business graph.\n"
    "Return ONLY valid JSON with this exact structure:\n"
    '{{"entities": [{{"id": "<slug>", "label": "<name>", "type": "<table|concept>"}}], '
    '"relationships": [{{"source": "<id>", "target": "<id>", "relation": "<verb|key>"}}]}}\n\n'
    "Tables:\n{tables_json}"
)


def extract_from_tables(path: str, max_rows_per_table: int = 50) -> dict:
    """Extract entities and relationships from CSV tables via LLM.

    Args:
        path: Folder path containing CSV files.
        max_rows_per_table: Max rows included per table in the LLM prompt.

    TODO: Add schema-aware examples and better prompt compression.
    TODO: Validate response with a typed model.
    """
    tables = extract_tables(path)
    preview = {
        table_name: rows[:max_rows_per_table]
        for table_name, rows in tables.items()
    }

    prompt = _TABLE_EXTRACTION_PROMPT.format(
        tables_json=json.dumps(preview, indent=2)
    )
    raw = call_llm(prompt)

    # Strip markdown code fences the model may wrap around JSON.
    clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean.strip(), flags=re.MULTILINE)

    try:
        result = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned non-JSON output: {exc}\nRaw response:\n{raw}"
        ) from exc

    if "entities" not in result or "relationships" not in result:
        raise ValueError(
            "LLM response missing required keys 'entities' or 'relationships'."
        )

    return result
