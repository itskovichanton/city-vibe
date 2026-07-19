from dataclasses import dataclass

from python.libs.entities.user import User


@dataclass
class UserCreatedEvent:
    """Пользователь создан."""

    user: User


@dataclass
class UserUpdatedEvent:
    """Профиль пользователя обновлён."""

    user: User


@dataclass
class UserStatusChangedEvent:
    """Изменён статус учётной записи."""

    user: User


@dataclass
class UserOnboardingCompletedEvent:
    """Онбординг завершён — сигнал для recommendation / AI-сервисов."""

    user: User
