"""Pydantic-модели HTTP-запросов (presenter)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GeoIn(BaseModel):
    latitude: float
    longitude: float


class PlaceCreateBody(BaseModel):
    name: str
    about: str
    category: str = Field(..., description="Код категории (PlaceCategory)")
    owner_id: int
    geo: GeoIn
    attrs: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: List[Dict[str, Any]] = Field(default_factory=list)


class PlacePatchBody(BaseModel):
    name: Optional[str] = None
    about: Optional[str] = None
    category: Optional[str] = None
    geo: Optional[GeoIn] = None
    attrs: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: Optional[List[Dict[str, Any]]] = None


class ProductCreateBody(BaseModel):
    place_id: int
    name: str
    description: str = ""
    price: Optional[float] = Field(
        None,
        ge=0,
        description="Цена в рублях; null = бесплатно / см. описание",
    )
    category: str = Field(..., description="Код категории (ProductCategory)")
    schedule: Optional[Dict[str, Any]] = None


class ProductPatchBody(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None


class CatalogMatchBody(BaseModel):
    prompt: str = Field(..., min_length=2, description="Вольное описание на естественном языке")
    catalog: Optional[str] = Field(
        None,
        description="product_categories | place_categories | cities",
    )
    entity_type: Optional[str] = Field(
        None,
        description="ProductCategoryInfo | PlaceCategoryInfo | City",
    )
    fields: Optional[List[str]] = Field(
        None,
        description="Поля строки, по которым матчить (плюс таблица алиасов)",
    )
    limit: int = Field(8, ge=1, le=50)
