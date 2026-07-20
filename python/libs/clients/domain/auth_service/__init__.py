"""DTO auth-service (без IoC)."""

from python.libs.clients.domain.auth_service.entities import (
    ChallengeOut,
    ForgotBody,
    GoogleBody,
    LoginBody,
    RefreshBody,
    RegisterBody,
    ResendBody,
    ResetBody,
    TokensOut,
    VerifyBody,
)

__all__ = [
    "RegisterBody",
    "VerifyBody",
    "LoginBody",
    "ResendBody",
    "ForgotBody",
    "ResetBody",
    "RefreshBody",
    "GoogleBody",
    "ChallengeOut",
    "TokensOut",
]
