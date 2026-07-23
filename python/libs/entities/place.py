from dataclasses import dataclass, field
from enum import StrEnum
from typing import List

from python.libs.entities.common import Entity, Contact, Rating
from python.libs.entities.geo import GeoLocation
from python.libs.entities.user import User


class PlaceCategory(StrEnum):
    """Категории мест, которые выбирает пользователь при онбординге."""

    BARS = "bars"  # Бары
    RESTAURANTS = "restaurants"  # Рестораны
    CAFES = "cafes"  # Кафе
    HOOKAH = "hookah"  # Кальянные
    CONCERTS = "concerts"  # Концерты
    THEATERS = "theaters"  # Театры
    PARKS = "parks"  # Парки
    EXHIBITIONS = "exhibitions"  # Выставки
    SPORTS = "sports"  # Спорт
    SHOPPING = "shopping"  # Шопинг
    CINEMA = "cinema"  # Кино
    NIGHTCLUBS = "nightclubs"  # Ночные клубы


@dataclass
class Place(Entity):
    geo: GeoLocation
    name: str
    about: str
    category: PlaceCategory
    owner: User
    rating: Rating = None
    contacts: List[Contact] = field(default_factory=list)
