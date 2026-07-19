"""Общий Redis-клиент (async). Нужен для rate-limit и idempotency."""

from __future__ import annotations

from typing import Protocol

import redis.asyncio as redis
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.infra.flags import flags


class RedisClient(Protocol):
    async def get(self, key: str) -> bytes | None: ...

    async def set(self, key: str, value: str | bytes, ex: int | None = None, nx: bool = False) -> bool | None: ...

    async def incr(self, key: str) -> int: ...

    async def expire(self, key: str, seconds: int) -> bool: ...

    async def close(self) -> None: ...


@bean
class RedisClientImpl(RedisClient):
    """Ленивый async Redis. Не коннектится, пока фичи не понадобятся."""

    _client: redis.Redis | None = None

    def init(self, **kwargs):
        self._client = None
        self._url = flags().redis_url

    def _raw(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self._url, decode_responses=False)
        return self._client

    async def get(self, key: str) -> bytes | None:
        return await self._raw().get(key)

    async def set(self, key: str, value: str | bytes, ex: int | None = None, nx: bool = False) -> bool | None:
        return await self._raw().set(key, value, ex=ex, nx=nx)

    async def incr(self, key: str) -> int:
        return int(await self._raw().incr(key))

    async def expire(self, key: str, seconds: int) -> bool:
        return bool(await self._raw().expire(key, seconds))

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
