"""Клиент и DTO user-service. Impl — из .client (не импортировать в тестах)."""

from python.libs.clients.domain.user_service.entities import (
    AvatarUploadOut,
    CreateUserBody,
    UpdateBioBody,
    UserOut,
)

__all__ = [
    "CreateUserBody",
    "UpdateBioBody",
    "UserOut",
    "AvatarUploadOut",
]
