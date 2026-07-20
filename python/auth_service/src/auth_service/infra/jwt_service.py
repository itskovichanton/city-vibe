"""JWT access/refresh токены."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

import jwt
from src.mybootstrap_ioc_itskovichanton.ioc import bean


class JwtService(Protocol):
    def create_access_token(self, account_id: int, user_id: int | None = None) -> tuple[str, int]: ...

    def create_refresh_token(self) -> tuple[str, str, datetime]: ...

    def decode_access_token(self, token: str) -> dict[str, Any]: ...

    def hash_refresh_token(self, token: str) -> str: ...


@bean(
    jwt_secret=("auth.jwt_secret", str, "dev-jwt-secret-change-me"),
    access_ttl_min=("auth.access_ttl_min", int, 15),
    refresh_ttl_days=("auth.refresh_ttl_days", int, 30),
)
class JwtServiceImpl(JwtService):
    """Секреты и TTL из config.yml через @bean."""

    jwt_secret: str = "dev-jwt-secret-change-me"
    access_ttl_min: int = 15
    refresh_ttl_days: int = 30

    def init(self, **kwargs):
        self.jwt_secret = kwargs.get("jwt_secret", getattr(self, "jwt_secret", "dev-jwt-secret-change-me"))
        self.access_ttl_min = int(kwargs.get("access_ttl_min", getattr(self, "access_ttl_min", 15)))
        self.refresh_ttl_days = int(kwargs.get("refresh_ttl_days", getattr(self, "refresh_ttl_days", 30)))

    def create_access_token(self, account_id: int, user_id: int | None = None) -> tuple[str, int]:
        expires_in = self.access_ttl_min * 60
        payload = {
            "sub": str(user_id if user_id is not None else account_id),
            "account_id": account_id,
            "user_id": user_id,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token, expires_in

    def create_refresh_token(self) -> tuple[str, str, datetime]:
        raw = secrets.token_urlsafe(48)
        expires = datetime.now(timezone.utc) + timedelta(days=self.refresh_ttl_days)
        return raw, self.hash_refresh_token(raw), expires

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
