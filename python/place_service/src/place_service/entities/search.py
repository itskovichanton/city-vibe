"""Модели и валидация запросов многокритериального поиска."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.libs.entities.place import PlaceCategory, ProductCategory
from python.place_service.src.place_service.infra.attr_ops import parse_attr_predicate


class SearchGeo(BaseModel):
    lat: float = Field(..., description="Широта точки пользователя (WGS-84)")
    lng: float = Field(..., description="Долгота точки пользователя (WGS-84)")


class SearchOpenInterval(BaseModel):
    open: str = Field(..., description="Время HH:MM — место/продукт доступен в этот момент")


class SearchOpenAt(BaseModel):
    weekday: int = Field(..., ge=0, le=6, description="День недели: 0=пн … 6=вс")
    intervals: List[SearchOpenInterval] = Field(
        ...,
        min_length=1,
        description="Интервалы: достаточно указать open",
    )


def _validate_tz(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = v.strip()
    if not s:
        return None
    try:
        ZoneInfo(s)
    except Exception as e:
        raise ValueError(f"Неизвестная таймзона: {s}") from e
    return s


class PlaceSearchRequest(BaseModel):
    """
    Поиск мест. Обязателен city_id; нужен хотя бы один якорь:
    category, name или open_at.
    """

    city_id: int = Field(..., description="ID города (обязательно)")
    category: Optional[str] = Field(None, description="Код PlaceCategory")
    name: Optional[str] = Field(None, description="Подстрока имени без учёта регистра")
    limit: int = Field(20, ge=1, le=100)
    page: int = Field(1, ge=1)
    sort_by: Optional[Literal["rating", "distance", "created_at"]] = Field(
        None,
        description="rating | distance (нужен my_geo) | created_at",
    )
    exclude_ids: List[int] = Field(
        default_factory=list,
        max_length=200,
        description="Не возвращать эти id мест",
    )
    open_at: Optional[List[SearchOpenAt]] = Field(None)
    my_geo: Optional[SearchGeo] = None
    timezone: Optional[str] = Field(
        None,
        description="IANA TZ для open_at / now (иначе timezone расписания места)",
    )
    attrs: Optional[Dict[str, Any]] = None

    @field_validator("category")
    @classmethod
    def _category_known(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        try:
            PlaceCategory(v)
        except ValueError as e:
            raise ValueError(f"Неизвестная категория: {v}") from e
        return v

    @field_validator("name")
    @classmethod
    def _name_strip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: Optional[str]) -> Optional[str]:
        return _validate_tz(v)

    @model_validator(mode="after")
    def _integrity(self) -> "PlaceSearchRequest":
        if not self.category and not self.name and not self.open_at:
            raise ValueError("Нужен хотя бы один якорь: category, name или open_at")
        if self.sort_by == "distance" and self.my_geo is None:
            raise ValueError("sort_by=distance требует my_geo")
        if self.open_at is not None and len(self.open_at) == 0:
            raise ValueError("open_at не должен быть пустым массивом")
        if self.attrs is not None:
            if not self.category:
                raise ValueError("attrs требуют category")
            if not isinstance(self.attrs, dict):
                raise ValueError("attrs должен быть объектом")
            for key, raw in self.attrs.items():
                parse_attr_predicate(key, raw)
        return self


class ProductSearchRequest(BaseModel):
    """
    Поиск товаров/услуг. Обязателен city_id (через place).
    Нужен якорь: category / q / place_id / place_name / place_category / date_from.
    """

    city_id: int = Field(..., description="ID города места")
    category: Optional[str] = Field(None, description="Код ProductCategory")
    q: Optional[str] = Field(None, description="Подстрока в name/description продукта или имени места")
    place_id: Optional[int] = Field(None, description="Только продукты этого места")
    place_name: Optional[str] = Field(None, description="Подстрока имени места")
    place_category: Optional[str] = Field(None, description="Категория места (cafes, gyms, …)")
    price_from: Optional[float] = Field(None, ge=0)
    price_to: Optional[float] = Field(None, ge=0)
    limit: int = Field(20, ge=1, le=100)
    page: int = Field(1, ge=1)
    sort_by: Optional[Literal["price", "distance", "created_at", "event_start"]] = Field(
        None,
        description="price | distance | created_at | event_start",
    )
    exclude_ids: List[int] = Field(
        default_factory=list,
        max_length=200,
        description="Не возвращать эти id продуктов",
    )
    exclude_place_ids: List[int] = Field(
        default_factory=list,
        max_length=200,
        description="Не возвращать продукты этих мест",
    )
    one_per_place: bool = Field(False, description="Не больше одного продукта на место")
    date_from: Optional[date] = Field(None, description="Пересечение с events/exceptions с этой даты")
    date_to: Optional[date] = Field(None, description="Пересечение с events/exceptions по эту дату")
    include_past: bool = Field(False, description="Включать события, которые уже закончились")
    timezone: Optional[str] = Field(None, description="IANA TZ для now / events")
    open_at: Optional[List[SearchOpenAt]] = None
    my_geo: Optional[SearchGeo] = None

    @field_validator("category")
    @classmethod
    def _product_category_known(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        try:
            ProductCategory(v)
        except ValueError as e:
            raise ValueError(f"Неизвестная категория продукта: {v}") from e
        return v

    @field_validator("place_category")
    @classmethod
    def _place_category_known(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        try:
            PlaceCategory(v)
        except ValueError as e:
            raise ValueError(f"Неизвестная категория места: {v}") from e
        return v

    @field_validator("q", "place_name")
    @classmethod
    def _strip_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        return s or None

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: Optional[str]) -> Optional[str]:
        return _validate_tz(v)

    @model_validator(mode="after")
    def _product_integrity(self) -> "ProductSearchRequest":
        if not any(
            [
                self.category,
                self.q,
                self.place_id,
                self.place_name,
                self.place_category,
                self.date_from,
            ]
        ):
            raise ValueError(
                "Нужен якорь: category, q, place_id, place_name, place_category или date_from"
            )
        if self.sort_by == "distance" and self.my_geo is None:
            raise ValueError("sort_by=distance требует my_geo")
        if self.price_from is not None and self.price_to is not None:
            if self.price_from > self.price_to:
                raise ValueError("price_from не может быть больше price_to")
        if self.open_at is not None and len(self.open_at) == 0:
            raise ValueError("open_at не должен быть пустым массивом")
        if self.date_from is not None and self.date_to is not None:
            if self.date_from > self.date_to:
                raise ValueError("date_from не может быть больше date_to")
        return self


def validate_search_request(body: PlaceSearchRequest) -> PlaceSearchRequest:
    if body.limit < 1 or body.page < 1:
        raise CoreException(message="limit и page должны быть >= 1")
    return body
