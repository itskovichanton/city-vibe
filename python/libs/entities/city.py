from dataclasses import dataclass

from python.libs.entities.base import Entity
from python.libs.entities.geo import GeoLocation


@dataclass
class City(Entity):
    geo: GeoLocation
    name: str
    about: str
