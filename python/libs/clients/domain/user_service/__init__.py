"""Клиент и DTO user-service. Сущности обновляй через: make openapi-user."""

from python.libs.clients.domain.user_service.client import (
    UserServiceClient,
    UserServiceClientImpl,
)
from python.libs.clients.domain.user_service.entities import (
    AvatarUploadOut,
    CreateUserBody,
    UpdateBioBody,
    UserOut,
)

__all__ = [
    "UserServiceClient",
    "UserServiceClientImpl",
    "CreateUserBody",
    "UpdateBioBody",
    "UserOut",
    "AvatarUploadOut",
]
