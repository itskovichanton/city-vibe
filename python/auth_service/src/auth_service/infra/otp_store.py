"""Хранилище OTP-challenge (Redis). In-memory — в otp_common."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.auth_service.src.auth_service.infra.otp_common import AuthOtpStore, OtpChallenge
from python.libs.infra.redis_client import RedisClient

# Re-export для обратной совместимости
from python.auth_service.src.auth_service.infra.otp_common import (  # noqa: F401
    InMemoryAuthOtpStore,
    generate_otp_code,
)

__all__ = [
    "AuthOtpStore",
    "OtpChallenge",
    "generate_otp_code",
    "InMemoryAuthOtpStore",
    "RedisAuthOtpStore",
]


def _key(challenge_id: str) -> str:
    return f"cityvibe:otp:{challenge_id}"


@bean(otp_ttl_sec=("auth.otp_ttl_sec", int, 300))
class RedisAuthOtpStore(AuthOtpStore):
    """Redis-реализация OTP store. TTL из config.yml auth.otp_ttl_sec."""

    redis_client: RedisClient
    otp_ttl_sec: int = 300

    def init(self, **kwargs):
        self.otp_ttl_sec = int(kwargs.get("otp_ttl_sec", getattr(self, "otp_ttl_sec", 300)))

    async def save(self, challenge: OtpChallenge, ttl_sec: int | None = None) -> None:
        ttl = ttl_sec or self.otp_ttl_sec
        payload = json.dumps(asdict(challenge), ensure_ascii=False)
        await self.redis_client.set(_key(challenge.challenge_id), payload, ex=ttl)

    async def get(self, challenge_id: str) -> Optional[OtpChallenge]:
        raw = await self.redis_client.get(_key(challenge_id))
        if raw is None:
            return None
        data = json.loads(raw.decode("utf-8"))
        return OtpChallenge(**data)

    async def delete(self, challenge_id: str) -> None:
        await self.redis_client.set(_key(challenge_id), "", ex=1)
