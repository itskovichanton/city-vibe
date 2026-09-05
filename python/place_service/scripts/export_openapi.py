"""Экспорт OpenAPI place-service."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from python.place_service.src.place_service.entities.search import PlaceSearchRequest, ProductSearchRequest

REPO_ROOT = Path(__file__).resolve().parents[3]


class GeoOut(BaseModel):
    latitude: float
    longitude: float


class CityOut(BaseModel):
    id: int
    name: str
    slug: str
    region: str = ""
    geo: Optional[GeoOut] = None
    is_major: bool = True
    sort_order: int = 0
    about: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CategoryOut(BaseModel):
    id: int
    code: str
    title: str
    title_en: str = ""
    icon_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class AttrSchemaOut(BaseModel):
    id: int
    category_code: str
    version: int = 1
    json_schema: Dict[str, Any]


class PlaceCreateBody(BaseModel):
    name: str
    about: str
    category: str
    owner_id: int
    geo: GeoOut
    attrs: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None


class PlaceOut(BaseModel):
    id: int
    name: str
    about: str
    category: str
    owner_id: int
    geo: GeoOut
    attrs: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None


class ProductCreateBody(BaseModel):
    place_id: int
    name: str
    description: str = ""
    price: Optional[float] = Field(None, description="Цена; null = бесплатно / см. описание")
    category: str
    schedule: Optional[Dict[str, Any]] = None


class ProductOut(BaseModel):
    id: int
    place_id: int
    name: str
    description: str = ""
    price: Optional[float] = None
    category: str
    schedule: Optional[Dict[str, Any]] = None
    place: Optional[Dict[str, Any]] = None
    distance_m: Optional[float] = None


def build_openapi_app() -> FastAPI:
    app = FastAPI(title="City Vibe — Place Service", version="1.0.0")

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "service": "place-service"}

    @app.get("/cities", tags=["cities"], response_model=List[CityOut])
    async def list_cities():
        raise NotImplementedError

    @app.get("/cities/{city_id}", tags=["cities"], response_model=CityOut)
    async def get_city(city_id: int):
        raise NotImplementedError

    @app.get("/categories", tags=["categories"], response_model=List[CategoryOut])
    async def list_categories():
        raise NotImplementedError

    @app.get("/product-categories", tags=["products"], response_model=List[CategoryOut])
    async def list_product_categories():
        raise NotImplementedError

    @app.get("/attr-schemas", tags=["attrs"], response_model=List[AttrSchemaOut])
    async def list_attr_schemas():
        raise NotImplementedError

    @app.get("/attr-schemas/{category_code}", tags=["attrs"], response_model=AttrSchemaOut)
    async def get_attr_schema(category_code: str):
        raise NotImplementedError

    @app.post("/places", tags=["places"], response_model=PlaceOut)
    async def create_place(body: PlaceCreateBody):
        raise NotImplementedError

    @app.get("/places", tags=["places"], response_model=List[PlaceOut])
    async def list_places(
        owner_id: Optional[int] = Query(None),
        category: Optional[str] = Query(None),
    ):
        raise NotImplementedError

    @app.post(
        "/places/search",
        tags=["places", "search"],
        summary="Многокритериальный поиск мест",
        description=(
            "Обязателен city_id; якорь category / name / open_at. "
            "Опционально timezone, exclude_ids, sort_by=rating|distance|created_at, "
            "open_at, my_geo, attrs."
        ),
    )
    async def search_places(body: PlaceSearchRequest):
        """См. PlaceSearchRequest / docs/api/places-search.md"""
        raise NotImplementedError

    @app.get("/places/{place_id}", tags=["places"], response_model=PlaceOut)
    async def get_place(place_id: int):
        raise NotImplementedError

    @app.patch("/places/{place_id}", tags=["places"], response_model=PlaceOut)
    async def patch_place(place_id: int, body: PlaceCreateBody):
        raise NotImplementedError

    @app.delete("/places/{place_id}", tags=["places"])
    async def delete_place(place_id: int):
        raise NotImplementedError

    @app.post("/products", tags=["products"], response_model=ProductOut)
    async def create_product(body: ProductCreateBody):
        raise NotImplementedError

    @app.get("/products", tags=["products"], response_model=List[ProductOut])
    async def list_products(
        place_id: Optional[int] = Query(None),
        category: Optional[str] = Query(None),
        limit: int = Query(100, ge=1, le=500),
    ):
        raise NotImplementedError

    @app.post(
        "/products/search",
        tags=["products", "search"],
        summary="Многокритериальный поиск продуктов",
        description=(
            "Обязателен city_id; якорь category / q / place_id / place_name / "
            "place_category / date_from. q ищет по продукту и имени места. "
            "exclude_ids vs exclude_place_ids, one_per_place, events, include_past=false, "
            "sort_by=price|distance|created_at|event_start (NULL price — NULLS LAST)."
        ),
    )
    async def search_products(body: ProductSearchRequest):
        """См. ProductSearchRequest / docs/api/products-search.md"""
        raise NotImplementedError

    @app.get("/products/{product_id}", tags=["products"], response_model=ProductOut)
    async def get_product(product_id: int):
        raise NotImplementedError

    @app.patch("/products/{product_id}", tags=["products"], response_model=ProductOut)
    async def patch_product(product_id: int, body: ProductCreateBody):
        raise NotImplementedError

    @app.delete("/products/{product_id}", tags=["products"])
    async def delete_product(product_id: int):
        raise NotImplementedError

    return app


def main() -> None:
    out = REPO_ROOT / "schema" / "openapi" / "place-service.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_openapi_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out}")
    old = REPO_ROOT / "schema" / "openapi" / "place-catalog.json"
    if old.exists():
        old.unlink()
        print(f"Удалён устаревший {old.name}")


if __name__ == "__main__":
    main()
