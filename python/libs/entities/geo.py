from dataclasses import dataclass


@dataclass
class GeoLocation:
    """Точные координаты пользователя для поиска мест вокруг"""
    latitude: float
    longitude: float
