"""События домена (payload для шины)."""

from python.libs.entities.events.auth import (
    AuthOtpRequestedEvent,
    AuthUserRegisteredEvent,
    TOPIC_AUTH_OTP_REQUESTED,
    TOPIC_AUTH_USER_REGISTERED,
)
from python.libs.entities.events.user import (
    UserCreatedEvent,
    UserOnboardingCompletedEvent,
    UserStatusChangedEvent,
    UserUpdatedEvent,
)

__all__ = [
    "UserCreatedEvent",
    "UserUpdatedEvent",
    "UserStatusChangedEvent",
    "UserOnboardingCompletedEvent",
    "AuthOtpRequestedEvent",
    "AuthUserRegisteredEvent",
    "TOPIC_AUTH_OTP_REQUESTED",
    "TOPIC_AUTH_USER_REGISTERED",
]
