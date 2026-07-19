from dataclasses import dataclass

from python.libs.dto.user import User


@dataclass
class UserCreatedEvent:
    user: User


@dataclass
class UserUpdatedEvent:
    user: User


@dataclass
class UserStatusChangedEvent:
    user: User
