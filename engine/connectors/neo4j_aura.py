"""Neo4j AuraDB connector helpers for OpenGraph extraction payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.config import get_optional_env
from engine.config import get_required_env
from engine.config import load_env_config


@dataclass(slots=True)
class Neo4jConnectionSettings:
    """Connection settings for Neo4j/AuraDB."""

    uri: str
    username: str
    password: str
    database: str = "neo4j"


def load_neo4j_settings(
    *,
    search_from: str | None = None,
) -> Neo4jConnectionSettings:
    """Load Neo4j connection values from env and local env files."""
    load_env_config(search_from=search_from)
    return Neo4jConnectionSettings(
        uri=get_required_env("NEO4J_URI", search_from=search_from),
        username=get_required_env("NEO4J_USERNAME", search_from=search_from),
        password=get_required_env("NEO4J_PASSWORD", search_from=search_from),
        database=get_optional_env("NEO4J_DATABASE", "neo4j", search_from=search_from)
        or "neo4j",
    )


def _sanitize_node_properties(entity: dict[str, Any]) -> dict[str, Any]:
    """Return persisted node properties excluding structural keys."""
    props = dict(entity.get("properties", {}))
    for key, value in entity.items():
        if key not in {"id", "label", "type", "properties"}:
            props[key] = value
    props.pop("dataset", None)
    return props


def _sanitize_relationship_properties(relationship: dict[str, Any]) -> dict[str, Any]:
    """Return persisted relationship properties excluding structural keys."""
    props = dict(relationship.get("properties", {}))
    for key, value in relationship.items():
        if key not in {"source", "target", "relation", "properties"}:
            props[key] = value
    props.pop("dataset", None)
    return props


def _dataset_cleanup_query() -> str:
    return """
    MATCH (n:Entity {dataset: $dataset})
    DETACH DELETE n
    """


def _upsert_node_query() -> str:
    return """
    MERGE (n:Entity {dataset: $dataset, id: $id})
    SET n.label = $label,
        n.type = $type,
        n += $properties
    """


def _upsert_relationship_query() -> str:
    return """
    MATCH (s:Entity {dataset: $dataset, id: $source})
    MATCH (t:Entity {dataset: $dataset, id: $target})
    MERGE (s)-[r:REL {dataset: $dataset, source: $source, target: $target, relation: $relation}]->(t)
    SET r += $properties
    """


def _export_nodes_query() -> str:
    return """
    MATCH (n:Entity {dataset: $dataset})
    RETURN n.id AS id,
           n.label AS label,
           n.type AS type,
           properties(n) AS props
    ORDER BY id
    """


def _export_relationships_query() -> str:
    return """
    MATCH (s:Entity {dataset: $dataset})-[r:REL {dataset: $dataset}]->(t:Entity {dataset: $dataset})
    RETURN r.source AS source,
           r.target AS target,
           r.relation AS relation,
           properties(r) AS props
    ORDER BY source, target, relation
    """


def _build_driver(settings: Neo4jConnectionSettings):
    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise RuntimeError(
            "neo4j driver is not installed. Install project dependencies first."
        ) from exc

    return GraphDatabase.driver(settings.uri, auth=(settings.username, settings.password))


def store_extraction_in_neo4j(
    extraction: dict[str, Any],
    *,
    dataset: str,
    settings: Neo4jConnectionSettings | None = None,
    clear_existing: bool = True,
) -> dict[str, int]:
    """Upsert extraction payload into Neo4j for one dataset namespace."""
    conn = settings or load_neo4j_settings()
    entities = extraction.get("entities", [])
    relationships = extraction.get("relationships", [])

    if not isinstance(entities, list) or not isinstance(relationships, list):
        raise ValueError("Extraction payload must include list keys: entities, relationships.")

    driver = _build_driver(conn)
    try:
        with driver.session(database=conn.database) as session:
            if clear_existing:
                session.run(_dataset_cleanup_query(), dataset=dataset)

            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                entity_id = str(entity.get("id", "")).strip()
                if not entity_id:
                    continue
                session.run(
                    _upsert_node_query(),
                    dataset=dataset,
                    id=entity_id,
                    label=str(entity.get("label") or entity_id),
                    type=str(entity.get("type") or "concept"),
                    properties=_sanitize_node_properties(entity),
                )

            for relationship in relationships:
                if not isinstance(relationship, dict):
                    continue
                source = str(relationship.get("source", "")).strip()
                target = str(relationship.get("target", "")).strip()
                relation = str(relationship.get("relation", "")).strip()
                if not source or not target or not relation:
                    continue
                session.run(
                    _upsert_relationship_query(),
                    dataset=dataset,
                    source=source,
                    target=target,
                    relation=relation,
                    properties=_sanitize_relationship_properties(relationship),
                )
    finally:
        driver.close()

    return {
        "node_count": sum(1 for item in entities if isinstance(item, dict) and item.get("id")),
        "edge_count": sum(
            1
            for item in relationships
            if isinstance(item, dict)
            and item.get("source")
            and item.get("target")
            and item.get("relation")
        ),
    }


def export_extraction_from_neo4j(
    *,
    dataset: str,
    settings: Neo4jConnectionSettings | None = None,
) -> dict[str, Any]:
    """Read one dataset namespace from Neo4j and return extraction JSON shape."""
    conn = settings or load_neo4j_settings()
    driver = _build_driver(conn)

    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    try:
        with driver.session(database=conn.database) as session:
            node_records = session.run(_export_nodes_query(), dataset=dataset)
            for record in node_records:
                props = dict(record["props"] or {})
                node_id = str(record["id"])
                label = str(record["label"] or node_id)
                node_type = str(record["type"] or "concept")
                for reserved in ("id", "label", "type", "dataset"):
                    props.pop(reserved, None)

                entity: dict[str, Any] = {
                    "id": node_id,
                    "label": label,
                    "type": node_type,
                }
                if props:
                    entity["properties"] = props
                entities.append(entity)

            rel_records = session.run(_export_relationships_query(), dataset=dataset)
            for record in rel_records:
                props = dict(record["props"] or {})
                source = str(record["source"])
                target = str(record["target"])
                relation = str(record["relation"])
                for reserved in ("source", "target", "relation", "dataset"):
                    props.pop(reserved, None)

                rel: dict[str, Any] = {
                    "source": source,
                    "target": target,
                    "relation": relation,
                }
                if props:
                    rel["properties"] = props
                relationships.append(rel)
    finally:
        driver.close()

    return {
        "entities": entities,
        "relationships": relationships,
        "metadata": {
            "dataset": dataset,
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "source_type": "neo4j",
        },
    }
