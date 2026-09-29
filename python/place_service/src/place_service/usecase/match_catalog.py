"""Подбор строк любого справочника по вольному описанию (без LLM)."""

from __future__ import annotations

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.place_service.src.place_service.infra.catalog_match import format_why, match_catalog_rows
from python.place_service.src.place_service.infra.catalog_registry import (
    CATALOGS,
    CatalogSpec,
    resolve_catalog,
)
from python.place_service.src.place_service.infra.orm.mappers import (
    category_to_api,
    city_dto_to_response,
    product_category_to_api,
)
from python.place_service.src.place_service.presenter.models import CatalogMatchBody
from python.place_service.src.place_service.repo.catalog_alias import CatalogAliasRepo
from python.place_service.src.place_service.repo.category import CategoryRepo
from python.place_service.src.place_service.repo.city import CityRepo
from python.place_service.src.place_service.repo.product_category import ProductCategoryRepo


class MatchCatalogUseCase(Protocol):
    async def execute(self, request: CatalogMatchBody) -> dict[str, Any]: ...


class ListCatalogsUseCase(Protocol):
    async def execute(self, _call: None = None) -> list[dict[str, Any]]: ...


@bean
class ListCatalogsUseCaseImpl(ListCatalogsUseCase):
    async def execute(self, _call: None = None) -> list[dict[str, Any]]:
        return [
            {
                "catalog": spec.code,
                "entity_type": spec.entity_type,
                "key_field": spec.key_field,
                "fields": list(spec.text_fields),
            }
            for spec in CATALOGS.values()
        ]


@bean
class MatchCatalogUseCaseImpl(MatchCatalogUseCase):
    product_category_repo: ProductCategoryRepo
    category_repo: CategoryRepo
    city_repo: CityRepo
    catalog_alias_repo: CatalogAliasRepo

    async def execute(self, request: CatalogMatchBody) -> dict[str, Any]:
        try:
            spec = resolve_catalog(request.catalog, request.entity_type)
        except ValueError as e:
            raise CoreException(message=str(e)) from e
        fields = _resolve_fields(spec, request.fields)
        rows = await self._load_rows(spec)
        aliases = await self.catalog_alias_repo.list_by_catalog(spec.code)
        hits = match_catalog_rows(
            request.prompt,
            rows,
            aliases,
            key_field=spec.key_field,
            fields=fields,
            limit=request.limit,
        )
        items = []
        for row, hit in hits:
            item = dict(row)
            item["why"] = format_why(hit)
            item["score"] = round(hit.score, 2)
            items.append(item)
        return {
            "catalog": spec.code,
            "entity_type": spec.entity_type,
            "prompt": request.prompt.strip(),
            "fields": list(fields),
            "items": items,
        }

    async def _load_rows(self, spec: CatalogSpec) -> list[dict[str, Any]]:
        if spec.code == "product_categories":
            return [product_category_to_api(c) for c in await self.product_category_repo.list_active()]
        if spec.code == "place_categories":
            return [category_to_api(c) for c in await self.category_repo.list_active()]
        if spec.code == "cities":
            out = []
            for city in await self.city_repo.list_major():
                resp = city_dto_to_response(city)
                out.append(
                    {
                        "id": resp.id,
                        "name": resp.name,
                        "slug": resp.slug,
                        "region": resp.region,
                        "is_major": resp.is_major,
                    }
                )
            return out
        raise CoreException(message=f"Справочник {spec.code} не загружается")


def _resolve_fields(spec: CatalogSpec, requested: list[str] | None) -> list[str]:
    allowed = list(spec.text_fields)
    if not requested:
        return allowed
    fields = []
    unknown = []
    for raw in requested:
        name = (raw or "").strip()
        if not name:
            continue
        if name not in allowed:
            unknown.append(name)
            continue
        if name not in fields:
            fields.append(name)
    if unknown:
        raise CoreException(
            message=f"Поля {unknown} нельзя матчить в {spec.code}. Доступны: {allowed}",
        )
    if not fields:
        raise CoreException(message="Нужно хотя бы одно поле из справочника")
    return fields
