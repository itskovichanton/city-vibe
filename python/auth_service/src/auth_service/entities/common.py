"""DTO auth-service."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class RegisterRequest:
    name: str
    identifier: str
    password: str
    birthdate: Optional[date]
    city_id: int
    accept_terms: bool


@dataclass
class VerifyOtpRequest:
    challenge_id: str
    code: str


@dataclass
class LoginRequest:
    identifier: str
    password: str


@dataclass
class ForgotPasswordRequest:
    identifier: str
    channel: Optional[str] = None


@dataclass
class ResetPasswordRequest:
    reset_token: str
    new_password: str


@dataclass
class RefreshTokenRequest:
    refresh_token: str


@dataclass
class GoogleAuthRequest:
    id_token: str
    city_id: Optional[int] = None
    name: Optional[str] = None
    birthdate: Optional[date] = None


@dataclass
class AuthTokensResponse:
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
    user_id: Optional[int] = None
    account_id: Optional[int] = None


@dataclass
class ChallengeResponse:
    challenge_id: str
    channel: str
    destination_masked: str
    expires_in: int = 300
