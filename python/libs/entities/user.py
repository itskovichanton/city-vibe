from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum, auto
from typing import List, Optional

from python.libs.entities.base import Entity
from python.libs.entities.city import City


class UserRole(StrEnum):
    """Роли пользователей для разграничения прав доступа."""

    GUEST = auto()  # Гость (не зарегистрирован)
    REGULAR = auto()  # Обычный пользователь
    MODERATOR = auto()  # Модератор контента
    ADMIN = auto()  # Администратор системы


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


class PlaceCategory(StrEnum):
    """Категории мест, которые выбирает пользователь при онбординге."""

    BARS = "bars"  # Бары
    RESTAURANTS = "restaurants"  # Рестораны
    CAFES = "cafes"  # Кафе
    HOOKAH = "hookah"  # Кальянные
    CONCERTS = "concerts"  # Концерты
    THEATERS = "theaters"  # Театры
    PARKS = "parks"  # Парки
    EXHIBITIONS = "exhibitions"  # Выставки
    SPORTS = "sports"  # Спорт
    SHOPPING = "shopping"  # Шопинг
    CINEMA = "cinema"  # Кино
    NIGHTCLUBS = "nightclubs"  # Ночные клубы


@dataclass
class Contact(Entity):
    """Контактные данные с возможностью верификации."""

    type: ContactType
    value: str
    verified: bool


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
    # Любимые категории мест (онбординг)
    favorite_categories: List[PlaceCategory] = field(default_factory=list)
    contacts: List[Contact] = field(default_factory=list)
    devices: List[UserDevice] = field(default_factory=list)
    # Флаг завершения онбординга
    onboarding_completed: bool = False
