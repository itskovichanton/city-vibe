from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto, Enum


class Status(Enum):
    """Текущее состояние учётной записи."""

    ACTIVE = auto()  # Активен
    BANNED = auto()  # Заблокирован за нарушения
    DEACTIVATED = auto()  # Удалён или деактивирован самим пользователем
    FROZEN = auto()  # Временно заморожен (подозрительная активность)


class ContactType(StrEnum):
    EMAIL = auto()
    PHONE = auto()


class DevicePlatform(StrEnum):
    IOS = auto()
    ANDROID = auto()
    WEB = auto()


@dataclass
class Entity:
    id: int
    deleted: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Contact(Entity):
    """Контактные данные с возможностью верификации."""

    type: ContactType
    value: str
    verified: bool


@dataclass
class Rating:
    up_votes: int = 0
    down_votes: int = 0
