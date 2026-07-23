"""Общие DTO/миксины City Vibe."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum, auto
from typing import Any, Dict, List


class Status(Enum):
    """Текущее состояние учётной записи."""

    ACTIVE = auto()
    BANNED = auto()
    DEACTIVATED = auto()
    FROZEN = auto()


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


class HasAttrs:
    """
    Маркер-миксин: сущность поддерживает кастомные attrs (dict).

    Не dataclass — чтобы не ломать порядок полей при наследовании от Entity.
    Подкласс сам объявляет: attrs: Dict[str, Any] = field(default_factory=dict)
    """

    attrs: Dict[str, Any]


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


@dataclass
class Image(Entity):
    url: str


@dataclass
class Album(Entity):
    name: str
    album: List[Image] = field(default_factory=list)
