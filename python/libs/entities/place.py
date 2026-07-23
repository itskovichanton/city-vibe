"""Места, категории, схемы attrs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional

from python.libs.entities.common import Album, Contact, Entity, HasAttrs, Rating
from python.libs.entities.geo import GeoLocation
from python.libs.entities.schedule import WeeklySchedule


class PlaceCategory(StrEnum):
    """Коды категорий мест (seed → place_categories). Источник истины в БД — title."""

    BARS = "bars"
    RESTAURANTS = "restaurants"
    CAFES = "cafes"
    HOOKAH = "hookah"
    CONCERTS = "concerts"
    THEATERS = "theaters"
    PARKS = "parks"
    EXHIBITIONS = "exhibitions"
    SPORTS = "sports"
    SHOPPING = "shopping"
    CINEMA = "cinema"
    NIGHTCLUBS = "nightclubs"


# Человекочитаемые названия для seed / UI fallback
PLACE_CATEGORY_TITLES: Dict[PlaceCategory, str] = {
    PlaceCategory.BARS: "Бары",
    PlaceCategory.RESTAURANTS: "Рестораны",
    PlaceCategory.CAFES: "Кафе",
    PlaceCategory.HOOKAH: "Кальянные",
    PlaceCategory.CONCERTS: "Концерты",
    PlaceCategory.THEATERS: "Театры",
    PlaceCategory.PARKS: "Парки",
    PlaceCategory.EXHIBITIONS: "Выставки",
    PlaceCategory.SPORTS: "Спорт",
    PlaceCategory.SHOPPING: "Шопинг",
    PlaceCategory.CINEMA: "Кино",
    PlaceCategory.NIGHTCLUBS: "Ночные клубы",
}


@dataclass
class PlaceCategoryInfo(Entity):
    """Строка справочника place_categories."""

    code: str
    title: str
    title_en: str = ""
    icon_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


@dataclass
class AttrSchema(Entity):
    """JSON Schema кастомных attrs для категории (1:1 с place_categories)."""

    category_code: str
    json_schema: Dict[str, Any]
    version: int = 1


@dataclass
class Place(Entity, HasAttrs):
    """Место на карте (ресторан, бар, зал и т.д.)."""

    geo: GeoLocation
    name: str
    about: str
    category: PlaceCategory
    owner_id: int
    rating: Optional[Rating] = None
    album: Optional[Album] = None
    contacts: List[Contact] = field(default_factory=list)
    attrs: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[WeeklySchedule] = None
    pin_style_id: Optional[int] = None  # design-service map_pin_styles.id
    chat_theme_id: Optional[int] = None  # design-service chat_themes.id
    city_id: Optional[int] = None
