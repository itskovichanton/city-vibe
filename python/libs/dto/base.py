from dataclasses import dataclass
from datetime import datetime


@dataclass
class Entity:
    id: int
    deleted: bool
    created_at: datetime
    updated_at: datetime
