"""DTO place-catalog для HTTP-клиента."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GeoOut:
    latitude: float
    longitude: float


@dataclass
class CityOut:
    id: int
    name: str
    slug: str
    region: str = ""
    geo: GeoOut | None = None
    is_major: bool = True
    sort_order: int = 0
    about: str = ""
    created_at: str | None = None
    updated_at: str | None = None
