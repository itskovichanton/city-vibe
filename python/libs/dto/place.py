from dataclasses import dataclass, field
from typing import List

from python.libs.dto.base import Entity
from python.libs.dto.geo import GeoLocation
from python.libs.dto.user import Contact


@dataclass
class Place(Entity):
    geo: GeoLocation
    name: str
    about: str
    contacts: List[Contact] = field(default_factory=list)
