"""
HTTP-клиент user-service (Spring-like: Protocol + @bean Impl).

Интерфейс `UserServiceClient` — контракт для DI.
Реализация `UserServiceClientImpl` — httpx async-клиент.
"""

from __future__ import annotations

from typing import Protocol

import httpx
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.domain.user_service.entities import CreateUserBody, UpdateBioBody


class UserServiceClient(Protocol):
    """Контракт клиента user-service (инжектить именно его)."""

    async def health(self) -> dict:
        """Healthcheck сервиса."""
        ...

    async def create_user(self, body: CreateUserBody) -> dict:
        """Создать пользователя (онбординг, шаг 1)."""
        ...

    async def get_user(self, user_id: int) -> dict:
        """Получить профиль по id."""
        ...

    async def update_bio(self, user_id: int, body: UpdateBioBody) -> dict:
        """Обновить развёрнутое bio (онбординг, шаг 2)."""
        ...

    async def complete_onboarding(self, user_id: int) -> dict:
        """Завершить онбординг (шаг 3)."""
        ...

    async def upload_avatar(
        self,
        user_id: int,
        filename: str,
        data: bytes,
        content_type: str = "image/jpeg",
    ) -> dict:
        """Загрузить аватарку и привязать к профилю."""
        ...

    async def close(self) -> None:
        """Закрыть HTTP-соединения."""
        ...


@bean(
    base_url=("user-service.url", str, "http://localhost:8081"),
    timeout=("user-service.timeout", float, 30.0),
)
class UserServiceClientImpl(UserServiceClient):
    """
    Реализация UserServiceClient поверх httpx.AsyncClient.

    base_url / timeout берутся из config.yml (секция user-service)
    через аргументы декоратора @bean(...).
    """

    _http: httpx.AsyncClient | None = None

    def init(self, **kwargs):
        self.base_url = str(kwargs.get("base_url", getattr(self, "base_url", "http://localhost:8081"))).rstrip("/")
        self.timeout = float(kwargs.get("timeout", getattr(self, "timeout", 30.0)))
        self._http = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    def _client(self) -> httpx.AsyncClient:
        assert self._http is not None, "UserServiceClientImpl не инициализирован"
        return self._http

    async def health(self) -> dict:
        r = await self._client().get("/health")
        r.raise_for_status()
        return r.json()

    async def create_user(self, body: CreateUserBody) -> dict:
        payload = {
            "name": body.name,
            "age": body.age,
            "short_bio": body.short_bio or "",
            "favorite_categories": body.favorite_categories or [],
        }
        r = await self._client().post("/users", json=payload)
        r.raise_for_status()
        return r.json()

    async def get_user(self, user_id: int) -> dict:
        r = await self._client().get(f"/users/{user_id}")
        r.raise_for_status()
        return r.json()

    async def update_bio(self, user_id: int, body: UpdateBioBody) -> dict:
        r = await self._client().put(f"/users/{user_id}/bio", json={"long_bio": body.long_bio})
        r.raise_for_status()
        return r.json()

    async def complete_onboarding(self, user_id: int) -> dict:
        r = await self._client().post(f"/users/{user_id}/onboarding/complete")
        r.raise_for_status()
        return r.json()

    async def upload_avatar(
        self,
        user_id: int,
        filename: str,
        data: bytes,
        content_type: str = "image/jpeg",
    ) -> dict:
        r = await self._client().post(
            f"/users/{user_id}/avatar",
            files={"file": (filename, data, content_type)},
        )
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None
