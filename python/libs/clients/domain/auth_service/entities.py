"""DTO auth-service для HTTP-клиента (см. schema/openapi/auth-service.json)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RegisterBody:
    name: str
    identifier: str
    password: str
    city_id: int
    accept_terms: bool
    birthdate: str | None = None


@dataclass
class VerifyBody:
    challenge_id: str
    code: str


@dataclass
class LoginBody:
    identifier: str
    password: str


@dataclass
class ResendBody:
    challenge_id: str


@dataclass
class ForgotBody:
    identifier: str
    channel: str | None = None


@dataclass
class ResetBody:
    reset_token: str
    new_password: str


@dataclass
class RefreshBody:
    refresh_token: str


@dataclass
class GoogleBody:
    id_token: str
    city_id: int | None = None
    name: str | None = None
    birthdate: str | None = None


@dataclass
class ChallengeOut:
    challenge_id: str
    channel: str
    destination_masked: str
    expires_in: int = 300


@dataclass
class TokensOut:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    user_id: int | None = None
    account_id: int | None = None
