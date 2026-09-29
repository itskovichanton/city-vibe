"""Подбор строк справочника по вольному тексту — без LLM."""

from python.place_service.src.place_service.infra.catalog_aliases_data import all_alias_rows
from python.place_service.src.place_service.infra.catalog_match import (
    CatalogAlias,
    format_why,
    match_catalog_rows,
)
from python.place_service.src.place_service.infra.catalog_registry import resolve_catalog


def _aliases(catalog: str) -> list[CatalogAlias]:
    return [
        CatalogAlias(*row)
        for row in all_alias_rows()
        if row[0] == catalog
    ]


def test_resolve_entity_type():
    spec = resolve_catalog(None, "ProductCategoryInfo")
    assert spec.code == "product_categories"
    spec2 = resolve_catalog("place_categories", None)
    assert spec2.entity_type == "PlaceCategoryInfo"


def test_sweet_and_sport_product_categories():
    rows = [
        {"code": "bakery_goods", "title": "Выпечка", "title_en": "Bakery"},
        {"code": "coffee", "title": "Кофе", "title_en": "Coffee"},
        {"code": "yoga_class", "title": "Занятие йогой", "title_en": "Yoga"},
        {"code": "dance_class", "title": "Танцевальное занятие", "title_en": "Dance"},
        {"code": "sport_goods", "title": "Спортивные товары", "title_en": "Sport"},
        {"code": "fitness_class", "title": "Фитнес-занятие", "title_en": "Fitness"},
        {"code": "construction", "title": "Строительные товары", "title_en": "Construction"},
        {"code": "plumbing", "title": "Сантехника", "title_en": "Plumbing"},
    ]
    hits = match_catalog_rows(
        "люблю сладенькое и спортом заниматься",
        rows,
        _aliases("product_categories"),
        key_field="code",
        fields=["title"],
        limit=8,
    )
    codes = {row["code"] for row, _ in hits}
    assert "bakery_goods" in codes
    assert "coffee" in codes
    assert "yoga_class" in codes
    assert "dance_class" in codes
    assert "sport_goods" in codes
    assert "construction" not in codes
    assert "plumbing" not in codes
    for row, hit in hits:
        why = format_why(hit)
        assert why
        assert row["code"]


def test_title_field_match_without_alias():
    rows = [{"code": "coffee", "title": "Кофе", "title_en": "Coffee"}]
    hits = match_catalog_rows(
        "хочу кофе",
        rows,
        [],
        key_field="code",
        fields=["title"],
        limit=5,
    )
    assert len(hits) == 1
    assert hits[0][0]["code"] == "coffee"
    assert "title" in format_why(hits[0][1])


def test_sweet_and_photoshoot_colloquial():
    rows = [
        {"code": "photo_session", "title": "Фотосессия", "title_en": "Photo session"},
        {"code": "bakery_goods", "title": "Выпечка", "title_en": "Bakery"},
        {"code": "coffee", "title": "Кофе", "title_en": "Coffee"},
        {"code": "plumbing", "title": "Сантехника", "title_en": "Plumbing"},
    ]
    hits = match_catalog_rows(
        "я люблю сладкое и фоткаться",
        rows,
        _aliases("product_categories"),
        key_field="code",
        fields=["title"],
        limit=8,
    )
    codes = {row["code"] for row, _ in hits}
    assert "photo_session" in codes
    assert "bakery_goods" in codes
    assert "plumbing" not in codes


def test_city_nicknames():
    rows = [
        {"slug": "novosibirsk", "name": "Новосибирск", "region": "Новосибирская область"},
        {"slug": "moskva", "name": "Москва", "region": "Москва"},
    ]
    hits = match_catalog_rows(
        "что интересного в нск",
        rows,
        _aliases("cities"),
        key_field="slug",
        fields=["name"],
        limit=3,
    )
    assert hits
    assert hits[0][0]["slug"] == "novosibirsk"
    assert "Новосибирск" in format_why(hits[0][1]) or "алиас" in format_why(hits[0][1]).lower() or "город" in format_why(hits[0][1]).lower()
