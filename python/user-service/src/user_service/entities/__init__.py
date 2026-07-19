"""DTO запросов/ответов user-service."""

from user_service.entities.common import (
    CompleteOnboardingRequest,
    CreateUserRequest,
    UpdateBioRequest,
    UserResponse,
)

__all__ = [
    "CreateUserRequest",
    "UpdateBioRequest",
    "CompleteOnboardingRequest",
    "UserResponse",
]
