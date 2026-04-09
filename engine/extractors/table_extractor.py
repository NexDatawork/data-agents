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

import random  # noqa: E402

from engine.llm.provider import call_llm_messages  # noqa: E402

# ── Prompts ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert data-modelling assistant. You receive structured summaries of
relational CSV tables and convert them into a knowledge-graph representation.

OUTPUT REQUIREMENTS (STRICT):
- Return ONLY valid JSON — no markdown fences, no explanation text.
- The JSON must have exactly two top-level keys: "entities" and "relationships".

JSON SHAPE:
{
  "entities": [
    {"id": "<slug>", "label": "<display_name>", "type": "<entity_type>"}
  ],
  "relationships": [
    {"source": "<entity_id>", "target": "<entity_id>", "relation": "<relation_label>"}
  ]
}

ENTITY RULES:
- Create one entity per UNIQUE real-world object across ALL tables
  (person, org, product, event, location, metric, concept, transaction, etc.).
- "id": lowercase slug using underscores, prefixed with table name to avoid
  collisions.  Example: "customers:c001", "products:prod_42".
- "label": human-readable name (preserve original capitalisation).
- "type": singular lowercase noun that describes the entity class.
  Derive from the table name when appropriate (table "orders" → type "order").
- Deduplicate entities that appear across multiple tables via FK references.

RELATIONSHIP RULES:
- Create a relationship for every meaningful link: FK references, implicit semantic
  connections (e.g. a sales row that ties a product to a customer), and any other
  domain-apparent connections.
- "source" and "target" MUST match an existing entity "id".
- "relation": short snake_case verb phrase.
  Examples: "placed_by", "contains", "located_in", "assigned_to", "belongs_to".
- Never produce duplicate relationships (same source + target + relation).
- Prefer meaningful verbs over raw column names.
"""

_USER_PROMPT_TEMPLATE = """\
Below are summaries of {table_count} relational table(s) from the same dataset.

For each table you receive:
  • row_count     — total data rows
  • primary_key   — the inferred primary-key column  (★ marked in Columns)
  • columns       — name, inferred value type, uniqueness %, FK hint if detected (→ target)
  • sample_rows   — up to {max_rows} representative rows

{tables_text}
Extract the knowledge graph following the rules in the system prompt.
Aim to capture the most important entities and every meaningful relationship.
"""

# ── Column-type inference ─────────────────────────────────────────────────────

_DATE_RE = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}")
_BOOL_VALS = frozenset({"true", "false", "yes", "no", "1", "0", "y", "n", "t", "f"})


def _infer_column_type(values: list[str]) -> str:
    """Infer a simple value type: id | numeric | date | boolean | text."""
    non_empty = [v for v in values if v][:100]
    if not non_empty:
        return "text"

    numeric_count = sum(1 for v in non_empty if re.fullmatch(r"-?\d+(\.\d+)?", v))
    if numeric_count / len(non_empty) > 0.8:
        return "numeric"

    date_count = sum(1 for v in non_empty if _DATE_RE.search(v))
    if date_count / len(non_empty) > 0.7:
        return "date"

    if all(v.lower() in _BOOL_VALS for v in non_empty):
        return "boolean"

    # High-cardinality short values → identifier
    avg_len = sum(len(v) for v in non_empty) / len(non_empty)
    if _unique_ratio(non_empty) > 0.85 and avg_len <= 24:
        return "id"

    return "text"


# ── Table summarisation ───────────────────────────────────────────────────────

def _format_table_summary(
    table_name: str,
    rows: list[dict[str, str]],
    pk_col: str,
    fk_hints: dict[str, str],
    max_rows: int,
) -> str:
    """Return a compact text block describing one table for the LLM prompt."""
    if not rows:
        return f"TABLE: {table_name}\n  (empty)\n"

    columns = list(rows[0].keys())
    row_count = len(rows)

    # Column metadata lines
    col_lines: list[str] = []
    for col in columns:
        vals = _column_values(rows, col)
        col_type = _infer_column_type(vals)
        uniqueness = f"{_unique_ratio(vals) * 100:.0f}% unique" if vals else "no data"
        pk_marker = " ★ PK" if col == pk_col else ""
        fk_ref = fk_hints.get(col)
        fk_marker = f" → {fk_ref}" if fk_ref else ""
        col_lines.append(f"    - {col} [{col_type}] ({uniqueness}){pk_marker}{fk_marker}")

    # Sample rows: first 3 + random picks for variety
    sample: list[dict[str, str]] = list(rows[:3])
    remaining = rows[3:]
    if remaining and len(sample) < max_rows:
        extra = random.sample(remaining, min(max_rows - len(sample), len(remaining)))
        sample.extend(extra)

    header = " | ".join(columns)
    divider = "-" * min(len(header), 120)
    sample_lines = [header, divider] + [
        " | ".join(row.get(c, "") for c in columns) for row in sample
    ]
    sample_text = "\n    ".join(sample_lines)

    fk_col_names = [c for c in columns if c in fk_hints]
    fk_text = (
        ", ".join(f"{c} → {fk_hints[c]}" for c in fk_col_names)
        if fk_col_names
        else "(none inferred)"
    )

    return (
        f"TABLE: {table_name} ({row_count} rows)\n"
        f"  Primary key: {pk_col}\n"
        f"  Columns:\n"
        + "\n".join(col_lines)
        + f"\n  Foreign-key hints: {fk_text}\n"
        f"  Sample rows (showing {len(sample)} of {row_count}):\n"
        f"    {sample_text}\n"
    )


def _build_tables_text(
    tables: dict[str, list[dict[str, str]]],
    primary_keys: dict[str, str],
    fk_targets: dict[str, str],
    max_rows: int,
) -> str:
    """Build the full tables section of the LLM user prompt."""
    parts: list[str] = []
    for table_name, rows in tables.items():
        pk_col = primary_keys.get(table_name, "")
        sample_cols = list(rows[0].keys()) if rows else []
        fk_hints = {col: fk_targets[col] for col in sample_cols if col in fk_targets}
        parts.append(_format_table_summary(table_name, rows, pk_col, fk_hints, max_rows))
    return "\n".join(parts)


# ── Response validation ───────────────────────────────────────────────────────

def _validate_and_clean_llm_result(raw_result: dict) -> dict:
    """Validate and normalise the LLM JSON result.

    - Removes malformed entities / relationships.
    - Normalises ids to safe slug format.
    - Drops relationships whose endpoints are not in the entity list.
    - Deduplicates relationships.

    Raises ValueError if the top-level structure is wrong.
    """
    if not isinstance(raw_result, dict):
        raise ValueError("LLM result is not a JSON object.")
    if "entities" not in raw_result or "relationships" not in raw_result:
        raise ValueError("LLM result missing 'entities' or 'relationships' key.")

    valid_entities: list[dict] = []
    entity_ids: set[str] = set()

    for ent in raw_result.get("entities", []):
        if not isinstance(ent, dict):
            continue
        if not ent.get("id") or not ent.get("type"):
            continue
        ent["id"] = re.sub(r"[^a-z0-9:_-]+", "_", str(ent["id"]).lower()).strip("_")
        ent.setdefault("label", ent["id"])
        valid_entities.append(ent)
        entity_ids.add(ent["id"])

    valid_rels: list[dict] = []
    seen_sigs: set[tuple[str, str, str]] = set()

    for rel in raw_result.get("relationships", []):
        if not isinstance(rel, dict):
            continue
        src = re.sub(r"[^a-z0-9:_-]+", "_", str(rel.get("source", "")).lower()).strip("_")
        tgt = re.sub(r"[^a-z0-9:_-]+", "_", str(rel.get("target", "")).lower()).strip("_")
        rel_type = str(rel.get("relation", "")).strip()
        if not src or not tgt or not rel_type:
            continue
        # Drop dangling references
        if src not in entity_ids or tgt not in entity_ids:
            continue
        sig = (src, tgt, rel_type)
        if sig in seen_sigs:
            continue
        seen_sigs.add(sig)
        valid_rels.append({"source": src, "target": tgt, "relation": rel_type})

    return {"entities": valid_entities, "relationships": valid_rels}


# ── Main LLM extraction function ──────────────────────────────────────────────

def extract_from_tables(
    path: str,
    max_rows_per_table: int = 10,
    model: str | None = None,
) -> dict:
    """Extract entities and relationships from CSV tables via LLM.

    Sends compact table summaries (schema + sample rows + FK hints) to the
    configured LLM using structured system + user messages and JSON output mode.
    Returns the same shape as ``extract_from_tables_offline`` so the two modes
    are drop-in compatible.

    Strategy:
    1. Discover all CSV files (recursive) and load them.
    2. Run offline heuristics (PK inference, FK candidate detection) to build
       structural hints that are injected into the prompt — the LLM does not
       need to guess column roles from scratch.
    3. Build a compact human-readable summary per table (column types, uniqueness
       stats, FK arrows, sample rows).
    4. Call the LLM with a system prompt + the table summaries.
       JSON mode is requested so the response is guaranteed parseable JSON.
    5. If parsing or validation fails, retry once with the error fed back to
       the model so it can self-correct.

    Args:
        path:               Folder containing CSV files (searched recursively).
        max_rows_per_table: Max sample rows included per table in the prompt.
                            Keep low (≤15) to stay within token limits for large datasets.
        model:              Override the LLM model (default: OPENAI_MODEL env var
                            or gpt-4o-mini).

    Returns:
        ``{"entities": [...], "relationships": [...]}`` — same shape as the
        offline extractor.

    Raises:
        EnvironmentError: If OPENAI_API_KEY is not set.
        ValueError:       If the LLM returns an invalid or unparseable response
                          after retries.
    """
    tables = extract_tables(path)

    # Reuse offline heuristics to provide FK/PK hints to the LLM.
    primary_keys: dict[str, str] = {
        name: _guess_primary_key(name, rows)
        for name, rows in tables.items()
    }
    pk_values_by_table: dict[str, set[str]] = {
        name: {
            _normalize_match_value(row.get(primary_keys[name]))
            for row in rows
            if _normalize_match_value(row.get(primary_keys[name]))
        }
        for name, rows in tables.items()
    }
    fk_targets: dict[str, str] = {}
    for tbl, pk_col in primary_keys.items():
        for candidate in _foreign_key_candidates(tbl, pk_col):
            fk_targets[candidate] = tbl

    tables_text = _build_tables_text(tables, primary_keys, fk_targets, max_rows_per_table)
    user_content = _USER_PROMPT_TEMPLATE.format(
        table_count=len(tables),
        max_rows=max_rows_per_table,
        tables_text=tables_text,
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            raw = call_llm_messages(messages, json_mode=(attempt == 0), model=model)
            # Strip accidental markdown fences (non-JSON mode fallback)
            clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
            clean = re.sub(r"\s*```$", "", clean.strip(), flags=re.MULTILINE)
            parsed = json.loads(clean)
            return _validate_and_clean_llm_result(parsed)
        except (ValueError, json.JSONDecodeError) as exc:
            last_exc = exc
            if attempt == 0:
                # Feed the error back so the model can self-correct on the second try.
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response could not be parsed: {exc}. "
                            "Please return ONLY valid JSON with exactly the keys "
                            "'entities' and 'relationships'."
                        ),
                    }
                )

    raise ValueError(
        f"LLM extraction failed after 2 attempts. Last error: {last_exc}"
    ) from last_exc
