from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum, auto
from typing import List

from python.libs.dto.base import Entity
from python.libs.dto.city import City


class UserRole(StrEnum):
    """Роли пользователей для разграничения прав доступа"""
    GUEST = auto()  # Гость (не зарегистрирован)
    REGULAR = auto()  # Обычный пользователь
    MODERATOR = auto()  # Модератор контента
    ADMIN = auto()  # Администратор системы


class Status(Enum):
    """Текущее состояние учетной записи"""
    ACTIVE = auto()  # Активен
    BANNED = auto()  # Заблокирован за нарушения
    DEACTIVATED = auto()  # Удален или деактивирован самим пользователем
    FROZEN = auto()  # Временно заморожен (подозрительная активность)


# Новые перечисления для контактов и устройств
class ContactType(StrEnum):
    EMAIL = auto()
    PHONE = auto()


class DevicePlatform(StrEnum):
    IOS = auto()
    ANDROID = auto()
    WEB = auto()


@dataclass
class Contact(Entity):
    """Контактные данные с возможностью верификации"""
    type: ContactType
    value: str
    verified: bool


@dataclass
class UserDevice(Entity):
    """Устройство пользователя для отправки push-уведомлений"""
    device_model: str  # Например: "iPhone 15 Pro", "Samsung SM-G991B"
    user_id: int  # Привязка к конкретному пользователю
    push_token: str  # Токен от Firebase (FCM) или APNS
    platform: DevicePlatform  # Операционная система
    last_active: datetime = None
    os_version: str = None  # Например: "iOS 17.4", "Android 14"
    app_version: str = None  # Помогает понять, почему пуш мог не дойти (старая версия приложения)


@dataclass
class User(Entity):
    status: Status
    about: str
    username: str
    name: str
    birthdate: datetime
    city: City
    avatarURL: str = None
    contacts: List[Contact] = field(default_factory=list)
    devices: List[UserDevice] = field(default_factory=list)
