from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, auto
from typing import List, Optional

from python.libs.entities.city import City
from python.libs.entities.common import Entity, DevicePlatform, Status
from python.libs.entities.place import Contact, PlaceCategory


class UserRole(StrEnum):
    """Роли пользователей для разграничения прав доступа."""

    GUEST = auto()  # Гость (не зарегистрирован)
    REGULAR = auto()  # Обычный пользователь
    MODERATOR = auto()  # Модератор контента
    ADMIN = auto()  # Администратор системы


@dataclass
class UserDevice(Entity):
    """Устройство пользователя для отправки push-уведомлений."""

    device_model: str  # Например: "iPhone 15 Pro"
    user_id: int
    push_token: str  # FCM / APNS
    platform: DevicePlatform
    last_active: Optional[datetime] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


@dataclass
class User(Entity):
    """Профиль пользователя City Vibe."""

    status: Status
    name: str
    # Короткое описание («Коротко о себе»)
    short_bio: str = ""
    # Развёрнутое описание в свободной форме
    long_bio: str = ""
    age: Optional[int] = None
    username: Optional[str] = None
    birthdate: Optional[datetime] = None
    city: Optional[City] = None
    # URL аватарки в S3
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.REGULAR
    city_id: Optional[int] = None
    auth_account_id: Optional[int] = None
    # Любимые категории мест (онбординг)
    favorite_categories: List[PlaceCategory] = field(default_factory=list)
    contacts: List[Contact] = field(default_factory=list)
    devices: List[UserDevice] = field(default_factory=list)
    # Флаг завершения онбординга
    onboarding_completed: bool = False
