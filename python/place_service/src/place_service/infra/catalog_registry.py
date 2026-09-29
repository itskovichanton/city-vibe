"""Реестр справочников, по которым работает catalog/match."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CatalogSpec:
    """Описание справочника: откуда строки и чем матчить."""

    code: str
    entity_type: str
    key_field: str
    text_fields: Tuple[str, ...]
    title_field: str


CATALOGS: Dict[str, CatalogSpec] = {
    "product_categories": CatalogSpec(
        code="product_categories",
        entity_type="ProductCategoryInfo",
        key_field="code",
        text_fields=("title", "title_en"),
        title_field="title",
    ),
    "place_categories": CatalogSpec(
        code="place_categories",
        entity_type="PlaceCategoryInfo",
        key_field="code",
        text_fields=("title", "title_en"),
        title_field="title",
    ),
    "cities": CatalogSpec(
        code="cities",
        entity_type="City",
        key_field="slug",
        text_fields=("name", "region"),
        title_field="name",
    ),
}

ENTITY_TO_CATALOG: Dict[str, str] = {
    spec.entity_type: spec.code for spec in CATALOGS.values()
}
ENTITY_TO_CATALOG.update(
    {
        "productcategoryinfo": "product_categories",
        "placecategoryinfo": "place_categories",
        "city": "cities",
    }
)


def resolve_catalog(catalog: str | None, entity_type: str | None) -> CatalogSpec:
    raw = (catalog or entity_type or "").strip()
    if not raw:
        raise ValueError("Нужен catalog или entity_type")
    if raw in CATALOGS:
        return CATALOGS[raw]
    mapped = ENTITY_TO_CATALOG.get(raw) or ENTITY_TO_CATALOG.get(raw.lower())
    if mapped and mapped in CATALOGS:
        return CATALOGS[mapped]
    raise ValueError(
        f"Неизвестный справочник {raw!r}. Доступны: {', '.join(CATALOGS)}"
    )
