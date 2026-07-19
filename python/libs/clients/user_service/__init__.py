"""Сгенерированный клиент и DTO user-service. Сущности обновляй через: make openapi-user."""

from python.libs.clients.user_service.client import UserServiceClient
from python.libs.clients.user_service.entities import (
    AvatarUploadOut,
    CreateUserBody,
    UpdateBioBody,
    UserOut,
)

__all__ = [
    "UserServiceClient",
    "CreateUserBody",
    "UpdateBioBody",
    "UserOut",
    "AvatarUploadOut",
]
