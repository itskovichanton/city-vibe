from dataclasses import dataclass, field
from typing import List

from python.libs.entities.base import Entity
from python.libs.entities.geo import GeoLocation
from python.libs.entities.user import Contact


@dataclass
class Place(Entity):
    geo: GeoLocation
    name: str
    about: str
    contacts: List[Contact] = field(default_factory=list)
