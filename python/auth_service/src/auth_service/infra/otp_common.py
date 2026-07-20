"""OTP types/helpers без @bean (для unit-тестов и use-case)."""

from __future__ import annotations

import secrets
from dataclasses import asdict, dataclass
from typing import Optional, Protocol


@dataclass
class OtpChallenge:
    """Данные OTP-challenge."""

    challenge_id: str
    code: str
    purpose: str  # register | login | reset
    channel: str  # sms | email
    destination: str
    account_id: int | None = None
    extra: dict | None = None


class AuthOtpStore(Protocol):
    async def save(self, challenge: OtpChallenge, ttl_sec: int) -> None: ...

    async def get(self, challenge_id: str) -> Optional[OtpChallenge]: ...

    async def delete(self, challenge_id: str) -> None: ...


def generate_otp_code() -> str:
    """6-значный OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


class InMemoryAuthOtpStore(AuthOtpStore):
    """In-memory OTP store для unit-тестов."""

    def __init__(self):
        self._store: dict[str, tuple[OtpChallenge, int]] = {}

    async def save(self, challenge: OtpChallenge, ttl_sec: int) -> None:
        self._store[challenge.challenge_id] = (challenge, ttl_sec)

    async def get(self, challenge_id: str) -> Optional[OtpChallenge]:
        row = self._store.get(challenge_id)
        return row[0] if row else None

    async def delete(self, challenge_id: str) -> None:
        self._store.pop(challenge_id, None)

    def challenge_as_dict(self, challenge: OtpChallenge) -> dict:
        return asdict(challenge)
