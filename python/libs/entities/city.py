from dataclasses import dataclass
from typing import Optional

from python.libs.entities.common import Entity
from python.libs.entities.geo import GeoLocation


@dataclass
class City(Entity):
    """Город справочника (place-service)."""

    name: str
    slug: str = ""
    about: str = ""
    geo: Optional[GeoLocation] = None
    region: str = ""
    is_major: bool = True
    sort_order: int = 0
