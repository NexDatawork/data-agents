"""Tests for text extraction helpers."""

from pathlib import Path

from engine.extractors.table_extractor import extract_from_tables_offline
from engine.extractors.text_extractor import extract_text, extract_from_text_offline


def test_extract_text_filters_empty_lines() -> None:
    assert extract_text("A\n\nB\n") == ["A", "B"]


def test_extract_from_text_offline_returns_required_keys() -> None:
    result = extract_from_text_offline("Alice works at Acme.")
    assert "entities" in result
    assert "relationships" in result


def test_extract_from_text_offline_finds_entities() -> None:
    result = extract_from_text_offline("Alice founded Acme Corporation in London.")
    labels = [e["label"] for e in result["entities"]]
    assert "Alice" in labels
    assert "Acme" in labels or "Acme Corporation" in labels


def test_extract_from_text_offline_finds_relationship() -> None:
    result = extract_from_text_offline("Alice founded Acme Corporation.")
    assert any(r["relation"] == "founded" for r in result["relationships"])


def test_extract_from_tables_offline_normalizes_headers_and_builds_fk_edges(tmp_path: Path) -> None:
    (tmp_path / "customers.csv").write_text(
        "\ufeffCustomer ID, Customer Name\nC001, Alice Chen\n",
        encoding="utf-8",
    )
    (tmp_path / "orders.csv").write_text(
        "Order ID, Customer ID, Order Date\nO1001, C001, 2026-03-01\n",
        encoding="utf-8",
    )

    result = extract_from_tables_offline(str(tmp_path))

    entities = {entity["id"]: entity for entity in result["entities"]}
    relationships = result["relationships"]

    assert "customers:c001" in entities
    assert entities["customers:c001"]["label"] == "Alice Chen"
    assert entities["customers:c001"]["properties"]["source_table"] == "customers"
    assert entities["customers:c001"]["properties"]["source_row"] == "1"

    assert any(
        rel["source"] == "orders:o1001"
        and rel["target"] == "customers:c001"
        and rel["relation"] == "customer"
        and rel["properties"]["source_column"] == "customer_id"
        for rel in relationships
    )


def test_extract_from_tables_offline_creates_reference_nodes_for_missing_fk_targets(
    tmp_path: Path,
) -> None:
    (tmp_path / "orders.csv").write_text(
        "order_id,customer_id\nO1001,C999\n",
        encoding="utf-8",
    )
    (tmp_path / "customers.csv").write_text(
        "customer_id,customer_name\nC001,Alice\n",
        encoding="utf-8",
    )

    result = extract_from_tables_offline(str(tmp_path))
    entities = {entity["id"]: entity for entity in result["entities"]}

    assert "customers:c999" in entities
    assert entities["customers:c999"]["properties"]["reference_only"] == "true"
    assert any(
        rel["source"] == "orders:o1001"
        and rel["target"] == "customers:c999"
        and rel["relation"] == "customer"
        for rel in result["relationships"]
    )


def test_extract_from_tables_offline_discovers_csvs_recursively(tmp_path: Path) -> None:
    nested = tmp_path / "uploads" / "march"
    nested.mkdir(parents=True)
    (nested / "products.csv").write_text(
        "product_id,product_name\nP001,Notebook\n",
        encoding="utf-8",
    )

    result = extract_from_tables_offline(str(tmp_path))

    assert any(entity["id"] == "products:p001" for entity in result["entities"])


def test_extract_from_tables_offline_uses_value_overlap_for_generic_foreign_keys(
    tmp_path: Path,
) -> None:
    (tmp_path / "vehicles.csv").write_text(
        "vehicle_code,vehicle_name\nV001,Delivery Van\n",
        encoding="utf-8",
    )
    (tmp_path / "parts.csv").write_text(
        "part_code,part_name\nP100,Brake Pad\n",
        encoding="utf-8",
    )
    (tmp_path / "maintenance.csv").write_text(
        "record_id,car_code,part_code,notes\nR001,V001,P100,Changed front pads\n",
        encoding="utf-8",
    )

    result = extract_from_tables_offline(str(tmp_path))

    assert any(
        rel["source"] == "maintenance:r001"
        and rel["target"] == "vehicles:v001"
        and rel["relation"] == "car"
        and rel["properties"]["inference"] == "name+value"
        for rel in result["relationships"]
    )
    assert any(
        rel["source"] == "vehicles:v001"
        and rel["target"] == "parts:p100"
        and rel["relation"] == "related_via_maintenance"
        for rel in result["relationships"]
    )
