from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, auto
from typing import List, Optional

from python.libs.entities.city import City
from python.libs.entities.common import Contact, DevicePlatform, Entity, Status
from python.libs.entities.place import PlaceCategory


class UserRole(StrEnum):
    """Роли пользователей для разграничения прав доступа."""

    GUEST = auto()
    REGULAR = auto()
    MODERATOR = auto()
    ADMIN = auto()
    ASSISTANT = auto()


class Gender(StrEnum):
    """Пол пользователя (обязательное поле профиля)."""

    MALE = "male"
    FEMALE = "female"


@dataclass
class UserDevice(Entity):
    """Устройство пользователя для отправки push-уведомлений."""

    device_model: str
    user_id: int
    push_token: str
    platform: DevicePlatform
    last_active: Optional[datetime] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


@dataclass
class User(Entity):
    """Профиль пользователя City Vibe."""

    status: Status
    name: str
    gender: Gender = Gender.MALE
    short_bio: str = ""
    long_bio: str = ""
    age: Optional[int] = None
    username: Optional[str] = None
    birthdate: Optional[datetime] = None
    city: Optional[City] = None
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.REGULAR
    city_id: Optional[int] = None
    auth_account_id: Optional[int] = None
    favorite_categories: List[PlaceCategory] = field(default_factory=list)
    contacts: List[Contact] = field(default_factory=list)
    devices: List[UserDevice] = field(default_factory=list)
    onboarding_completed: bool = False
