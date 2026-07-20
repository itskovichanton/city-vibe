"""DTO уровня API / use-case (dataclass). Не путать с ORM-моделями."""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from python.libs.entities.user import PlaceCategory, Status, UserRole


@dataclass
class CreateUserRequest:
    """Запрос на создание / первичное заполнение профиля (шаг 1 онбординга)."""

    name: str
    age: Optional[int] = None
    short_bio: str = ""
    favorite_categories: List[PlaceCategory] = field(default_factory=list)
    avatar_url: Optional[str] = None
    city_id: Optional[int] = None
    birthdate: Optional[date] = None
    auth_account_id: Optional[int] = None


@dataclass
class UpdateBioRequest:
    """Запрос на сохранение развёрнутого «о себе» (шаг 2 онбординга)."""

    user_id: int
    long_bio: str


@dataclass
class CompleteOnboardingRequest:
    """Завершение онбординга (шаг 3)."""

    user_id: int


@dataclass
class UserResponse:
    """Ответ API с профилем пользователя."""

    id: int
    name: str
    status: Status
    short_bio: str = ""
    long_bio: str = ""
    age: Optional[int] = None
    avatar_url: Optional[str] = None
    role: UserRole = UserRole.REGULAR
    favorite_categories: List[PlaceCategory] = field(default_factory=list)
    onboarding_completed: bool = False
    deleted: bool = False
    city_id: Optional[int] = None
    birthdate: Optional[date] = None
    auth_account_id: Optional[int] = None
