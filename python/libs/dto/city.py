from dataclasses import dataclass

from python.libs.dto.base import Entity
from python.libs.dto.geo import GeoLocation


@dataclass
class City(Entity):
    geo: GeoLocation
    name: str
    about: str
