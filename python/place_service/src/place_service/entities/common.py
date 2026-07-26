"""DTO уровня API place-service."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from python.libs.entities.geo import GeoLocation


@dataclass
class CityResponse:
    """Город в ответе API."""

    id: int
    name: str
    slug: str
    region: str = ""
    geo: Optional[GeoLocation] = None
    is_major: bool = True
    sort_order: int = 0
    about: str = ""
    deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Заполняется в GET /cities/nearest (метры до запрошенной точки).
    distance_m: Optional[float] = None
