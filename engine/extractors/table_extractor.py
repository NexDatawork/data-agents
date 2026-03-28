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
from collections import Counter
from itertools import combinations
from pathlib import Path


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def extract_table(path: str) -> list[dict[str, str]]:
    """Extract rows from a single CSV file.

    TODO: Handle malformed files and non-CSV formats.
    """
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, restval="")
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header row: {path}")

        normalized_rows: list[dict[str, str]] = []
        for raw_row in reader:
            row = {
                _normalize_column_name(key): _normalize_cell(value)
                for key, value in raw_row.items()
                if key is not None
            }
            # Skip fully blank rows to keep node counts deterministic.
            if any(value for value in row.values()):
                normalized_rows.append(row)

        return normalized_rows


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
    csv_files = sorted(
        csv_file
        for csv_file in folder.rglob("*.csv")
        if csv_file.is_file()
    )
    stem_counts = Counter(csv_file.stem for csv_file in csv_files)

    for csv_file in csv_files:
        table_key = _table_key(folder, csv_file, stem_counts)
        tables[table_key] = extract_table(str(csv_file))

    if not tables:
        raise ValueError(f"No CSV tables found in folder: {path}")

    return tables


def _slug(value: str) -> str:
    """Create a stable lowercase slug for entity ids."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


_REFERENCE_SUFFIXES = (
    "_id",
    "_key",
    "_code",
    "_number",
    "_no",
    "_ref",
    "_fk",
    "_uuid",
    "_vin",
)


def _normalize_cell(value: str | None) -> str:
    """Normalize raw CSV cell values into deterministic strings."""
    if value is None:
        return ""
    return value.strip()


def _normalize_column_name(value: str) -> str:
    """Normalize header names so FK/PK heuristics are consistent."""
    clean = value.lstrip("\ufeff").strip().lower()
    clean = re.sub(r"[^a-z0-9]+", "_", clean)
    return clean.strip("_")


def _table_key(root: Path, csv_file: Path, stem_counts: Counter[str]) -> str:
    """Return a stable table key for a CSV file within a folder tree."""
    if stem_counts[csv_file.stem] == 1:
        return _normalize_column_name(csv_file.stem)

    relative_no_suffix = csv_file.relative_to(root).with_suffix("")
    return "__".join(_normalize_column_name(part) for part in relative_no_suffix.parts)


def _singularize(table_name: str) -> str:
    """Return a simple singular form for table names."""
    if table_name.endswith("ies") and len(table_name) > 3:
        return f"{table_name[:-3]}y"
    if table_name.endswith("ses") and len(table_name) > 3:
        return table_name[:-2]
    if table_name.endswith("s") and len(table_name) > 1:
        return table_name[:-1]
    return table_name


def _normalize_match_value(value: str | None) -> str:
    """Normalize values for approximate cross-table identifier matching."""
    return _normalize_cell(value).casefold()


def _strip_reference_suffix(column: str) -> str:
    """Strip common identifier suffixes from a column name."""
    for suffix in _REFERENCE_SUFFIXES:
        if column.endswith(suffix):
            return column.removesuffix(suffix)
    return column


def _looks_like_reference_column(column: str) -> bool:
    """Return whether a column name looks like a foreign-key/reference field."""
    return column.endswith(_REFERENCE_SUFFIXES)


def _column_values(rows: list[dict[str, str]], column: str) -> list[str]:
    """Return non-empty values for a column in row order."""
    return [value for row in rows if (value := _normalize_cell(row.get(column)))]


def _unique_ratio(values: list[str]) -> float:
    """Return uniqueness ratio for a value collection."""
    if not values:
        return 0.0
    return len(set(values)) / len(values)


def _label_column(table_name: str, row: dict[str, str], pk_col: str) -> str:
    """Pick the most human-readable label column for a row."""
    singular = _singularize(table_name)
    preferred = (
        f"{singular}_name",
        "name",
        "title",
        f"{singular}_title",
    )
    for column in preferred:
        if row.get(column):
            return column

    fallback = next((k for k in row if k.endswith("_name") and row.get(k)), None)
    return fallback or pk_col


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
    singular = _singularize(table_name)

    def pk_score(column: str) -> tuple[float, float, float, str]:
        values = _column_values(rows, column)
        unique_ratio = _unique_ratio(values)
        non_empty_ratio = len(values) / len(rows)
        score = 0.0

        explicit_candidates = (
            f"{singular}_id",
            f"{table_name}_id",
            f"{singular}_key",
            f"{table_name}_key",
            f"{singular}_code",
            f"{table_name}_code",
            "id",
            "key",
            "code",
        )
        if column in explicit_candidates:
            score += 100.0
        elif column.endswith(("_id", "_key", "_code", "_uuid", "_vin")):
            score += 40.0

        if unique_ratio == 1.0 and values:
            score += 35.0
        else:
            score += unique_ratio * 25.0

        score += non_empty_ratio * 20.0

        if column == columns[0]:
            score += 5.0

        # Prefer compact identifier-like columns over verbose descriptions.
        avg_len = sum(len(value) for value in values) / len(values) if values else 999.0
        if avg_len <= 24:
            score += 5.0

        return (score, unique_ratio, non_empty_ratio, column)

    return max((pk_score(column) for column in columns))[3]


def _foreign_key_candidates(table_name: str, pk_col: str) -> set[str]:
    """Return possible FK column names that may refer to a table."""
    singular = _singularize(table_name)
    candidates = {
        pk_col,
        f"{singular}_id",
        f"{table_name}_id",
    }
    if pk_col.endswith("_key"):
        candidates.add(f"{pk_col[:-4]}id")
    return {_normalize_column_name(candidate) for candidate in candidates}


def _table_aliases(table_name: str, pk_col: str) -> set[str]:
    """Return alias tokens that may identify a table in FK column names."""
    aliases = {
        _normalize_column_name(table_name),
        _normalize_column_name(_singularize(table_name)),
        _normalize_column_name(_strip_reference_suffix(pk_col)),
    }
    expanded: set[str] = set()
    for alias in aliases:
        if not alias:
            continue
        expanded.add(alias)
        parts = [part for part in alias.split("_") if part]
        if parts:
            expanded.add(parts[-1])
    return expanded


def _name_similarity_score(column: str, target_table: str, pk_col: str) -> float:
    """Score how likely a column name points to a target table."""
    column_base = _normalize_column_name(_strip_reference_suffix(column))
    if not column_base:
        return 0.0

    aliases = _table_aliases(target_table, pk_col)
    if column_base in aliases:
        return 40.0

    score = 0.0
    base_tokens = set(column_base.split("_"))
    for alias in aliases:
        alias_tokens = set(alias.split("_"))
        if base_tokens & alias_tokens:
            score = max(score, 25.0)
        if column_base.endswith(alias) or alias.endswith(column_base):
            score = max(score, 30.0)
    return score


def _guess_foreign_key_target(
    table_name: str,
    column: str,
    rows: list[dict[str, str]],
    primary_keys: dict[str, str],
    pk_values_by_table: dict[str, set[str]],
) -> str | None:
    """Infer which table a column references using names and value overlap."""
    values = {_normalize_match_value(value) for value in _column_values(rows, column)}
    if not values:
        return None

    looks_reference = _looks_like_reference_column(column)
    best_table: str | None = None
    best_score = 0.0

    for candidate_table, pk_col in primary_keys.items():
        if candidate_table == table_name and not looks_reference:
            continue

        target_values = pk_values_by_table.get(candidate_table, set())
        if not target_values:
            continue

        overlap = len(values & target_values)
        if overlap == 0:
            continue

        overlap_ratio = overlap / len(values)
        name_score = _name_similarity_score(column, candidate_table, pk_col)
        score = name_score + overlap_ratio * 60.0

        if overlap_ratio == 1.0:
            score += 20.0
        if looks_reference:
            score += 10.0
        if candidate_table == table_name:
            score -= 15.0

        if score > best_score:
            best_score = score
            best_table = candidate_table

    threshold = 35.0 if looks_reference else 70.0
    return best_table if best_score >= threshold else None


def _relation_name_for_column(column: str, target_table: str) -> str:
    """Convert a column name into a readable relation label."""
    base = _normalize_column_name(_strip_reference_suffix(column))
    return base or _singularize(target_table)


def _append_relationship(
    relationships: list[dict],
    seen_relationships: set[tuple[str, str, str]],
    *,
    source: str,
    target: str,
    relation: str,
    properties: dict[str, str],
) -> None:
    """Append a relationship if not already seen."""
    signature = (source, target, relation)
    if signature in seen_relationships:
        return

    seen_relationships.add(signature)
    relationships.append(
        {
            "source": source,
            "target": target,
            "relation": relation,
            "properties": properties,
        }
    )


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

    pk_values_by_table: dict[str, set[str]] = {
        table_name: {
            _normalize_match_value(row.get(primary_keys[table_name]))
            for row in rows
            if _normalize_match_value(row.get(primary_keys[table_name]))
        }
        for table_name, rows in tables.items()
    }

    # Index possible reference targets by matching common FK naming variants.
    fk_targets: dict[str, str] = {}
    for table_name, pk_col in primary_keys.items():
        for candidate in _foreign_key_candidates(table_name, pk_col):
            fk_targets[candidate] = table_name

    entities: list[dict] = []
    relationships: list[dict] = []
    seen_entities: set[str] = set()
    seen_relationships: set[tuple[str, str, str]] = set()
    referenced_targets: dict[str, tuple[str, str]] = {}

    # Walk every table row to emit one entity plus zero or more FK relationships.
    for table_name, rows in tables.items():
        pk_col = primary_keys[table_name]
        singular = _singularize(table_name)

        for row_index, row in enumerate(rows, start=1):
            raw_pk = (row.get(pk_col) or "").strip()
            if raw_pk:
                node_id = f"{table_name}:{_slug(raw_pk)}"
            else:
                node_id = f"{table_name}:row-{row_index}"

            label_col = _label_column(table_name, row, pk_col)
            label = row.get(label_col, raw_pk or node_id)

            if node_id not in seen_entities:
                seen_entities.add(node_id)
                entities.append(
                    {
                        "id": node_id,
                        "label": label,
                        "type": singular,
                        "properties": {
                            "table": table_name,
                            "source_table": table_name,
                            "source_row": str(row_index),
                            "primary_key_column": pk_col,
                            "primary_key_value": raw_pk,
                            **row,
                        },
                    }
                )

            row_fk_refs: list[tuple[str, str, str, str]] = []

            # Treat non-primary *_id fields as possible foreign keys.
            for column, value in row.items():
                if column == pk_col:
                    continue
                fk_value = (value or "").strip()
                if not fk_value:
                    continue

                target_table = fk_targets.get(column)
                if target_table is None:
                    target_table = _guess_foreign_key_target(
                        table_name=table_name,
                        column=column,
                        rows=rows,
                        primary_keys=primary_keys,
                        pk_values_by_table=pk_values_by_table,
                    )
                if not target_table:
                    continue

                target_id = f"{target_table}:{_slug(fk_value)}"
                referenced_targets[target_id] = (target_table, fk_value)
                relation = _relation_name_for_column(column, target_table)
                _append_relationship(
                    relationships,
                    seen_relationships,
                    source=node_id,
                    target=target_id,
                    relation=relation,
                    properties={
                        "source_table": table_name,
                        "source_row": str(row_index),
                        "source_column": column,
                        "foreign_key_value": fk_value,
                        "inference": "name+value"
                        if column not in fk_targets
                        else "name",
                    },
                )
                row_fk_refs.append((column, relation, target_table, target_id))

            # Add generic association edges between referenced entities in the same row.
            for (left_column, _, _, left_target), (right_column, _, _, right_target) in combinations(
                row_fk_refs,
                2,
            ):
                _append_relationship(
                    relationships,
                    seen_relationships,
                    source=left_target,
                    target=right_target,
                    relation=f"related_via_{singular}",
                    properties={
                        "source_table": table_name,
                        "source_row": str(row_index),
                        "source_columns": f"{left_column},{right_column}",
                        "inference": "association",
                    },
                )

    # Create lightweight placeholder nodes for referenced IDs that have no row.
    for target_id, (target_table, fk_value) in sorted(referenced_targets.items()):
        if target_id in seen_entities:
            continue

        seen_entities.add(target_id)
        entities.append(
            {
                "id": target_id,
                "label": fk_value or target_id,
                "type": _singularize(target_table),
                "properties": {
                    "table": target_table,
                    "source_table": target_table,
                    "primary_key_column": primary_keys.get(target_table, "id"),
                    "primary_key_value": fk_value,
                    "reference_only": "true",
                },
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
