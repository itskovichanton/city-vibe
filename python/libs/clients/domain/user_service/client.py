"""
Минимальный async HTTP-клиент user-service.

Сгенерированные DTO — в entities.py (make openapi-user).
Полноценный openapi-python-client можно догенерировать тем же таргетом Makefile.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from python.libs.clients.user_service.entities import CreateUserBody, UpdateBioBody, UserOut


class UserServiceClient:
    """Тонкая обёртка над REST API user-service."""

    def __init__(self, base_url: str = "http://localhost:8081", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "UserServiceClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def health(self) -> dict:
        r = await self._client.get("/health")
        r.raise_for_status()
        return r.json()

    async def create_user(self, body: CreateUserBody) -> dict:
        payload = {
            "name": body.name,
            "age": body.age,
            "short_bio": body.short_bio or "",
            "favorite_categories": body.favorite_categories or [],
        }
        r = await self._client.post("/users", json=payload)
        r.raise_for_status()
        return r.json()

    async def get_user(self, user_id: int) -> dict:
        r = await self._client.get(f"/users/{user_id}")
        r.raise_for_status()
        return r.json()

    async def update_bio(self, user_id: int, body: UpdateBioBody) -> dict:
        r = await self._client.put(f"/users/{user_id}/bio", json={"long_bio": body.long_bio})
        r.raise_for_status()
        return r.json()

    async def complete_onboarding(self, user_id: int) -> dict:
        r = await self._client.post(f"/users/{user_id}/onboarding/complete")
        r.raise_for_status()
        return r.json()

    async def upload_avatar(self, user_id: int, filename: str, data: bytes, content_type: str = "image/jpeg") -> dict:
        r = await self._client.post(
            f"/users/{user_id}/avatar",
            files={"file": (filename, data, content_type)},
        )
        r.raise_for_status()
        return r.json()
