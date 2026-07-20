"""Геолокация — каноническая модель координат."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoLocation:
    """
    Точные координаты (WGS-84).

    Использовать везде вместо пар lat/lng в DTO.
    """

    latitude: float
    longitude: float

    @classmethod
    def of(cls, latitude: float | None, longitude: float | None) -> GeoLocation | None:
        if latitude is None or longitude is None:
            return None
        return cls(latitude=float(latitude), longitude=float(longitude))
