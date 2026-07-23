"""Модели и валидация запроса многокритериального поиска мест."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.libs.entities.place import PlaceCategory
from python.place_service.src.place_service.infra.attr_ops import parse_attr_predicate


class SearchGeo(BaseModel):
    lat: float = Field(..., description="Широта точки пользователя (WGS-84)")
    lng: float = Field(..., description="Долгота точки пользователя (WGS-84)")


class SearchOpenInterval(BaseModel):
    open: str = Field(..., description="Время HH:MM — место должно быть открыто в этот момент")


class SearchOpenAt(BaseModel):
    weekday: int = Field(..., ge=0, le=6, description="День недели: 0=пн … 6=вс")
    intervals: List[SearchOpenInterval] = Field(
        ...,
        min_length=1,
        description="Интервалы: достаточно указать open — проверяем, что место открыто в это время",
    )


class PlaceSearchRequest(BaseModel):
    """
    Многокритериальный поиск мест.

    Обязательны: city_id, category.
    Остальное опционально; limit=20, page=1 по умолчанию.
    """

    city_id: int = Field(..., description="ID города (обязательно)")
    category: str = Field(..., description="Код категории PlaceCategory (обязательно)")
    name: Optional[str] = Field(None, description="Подстрока имени без учёта регистра")
    limit: int = Field(20, ge=1, le=100, description="Размер страницы (default 20)")
    page: int = Field(1, ge=1, description="Номер страницы с 1 (default 1)")
    sort_by: Optional[Literal["rating", "distance"]] = Field(
        None,
        description="Сортировка: rating (по рейтингу) или distance (нужен my_geo)",
    )
    open_at: Optional[List[SearchOpenAt]] = Field(
        None,
        description="Место должно быть открыто во ВСЕ указанные моменты (AND)",
    )
    my_geo: Optional[SearchGeo] = Field(
        None,
        description="Гео пользователя — для sort_by=distance и поля distance_m в ответе",
    )
    attrs: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Фильтры по кастомным attrs категории. Значение — скаляр (exact) "
            "или {operation, args}: between | or | and"
        ),
    )

    @field_validator("category")
    @classmethod
    def _category_known(cls, v: str) -> str:
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

    @model_validator(mode="after")
    def _integrity(self) -> "PlaceSearchRequest":
        if self.sort_by == "distance" and self.my_geo is None:
            raise ValueError("sort_by=distance требует my_geo")
        if self.open_at is not None and len(self.open_at) == 0:
            raise ValueError("open_at не должен быть пустым массивом (или не передавайте поле)")
        if self.attrs is not None:
            if not isinstance(self.attrs, dict):
                raise ValueError("attrs должен быть объектом")
            for key, raw in self.attrs.items():
                parse_attr_predicate(key, raw)
        return self


def validate_search_request(body: PlaceSearchRequest) -> PlaceSearchRequest:
    if body.limit < 1 or body.page < 1:
        raise CoreException(message="limit и page должны быть >= 1")
    return body
