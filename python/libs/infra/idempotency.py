"""
Idempotency-Key: кэш ответа в Redis по ключу.

ENV: CITYVIBE_IDEMPOTENCY_ENABLED=true
Header: Idempotency-Key (или CITYVIBE_IDEMPOTENCY_HEADER)
"""

from __future__ import annotations

import hashlib
import json
from typing import Callable

from fastapi import Request
from src.mybootstrap_core_itskovichanton.di import injector
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from python.libs.infra.flags import flags
from python.libs.infra.redis_client import RedisClient


def _redis() -> RedisClient:
    return injector().inject(RedisClient)


def _cache_key(scope: str, idem_key: str) -> str:
    digest = hashlib.sha256(f"{scope}:{idem_key}".encode()).hexdigest()
    return f"cityvibe:idem:{digest}"


async def idempotency_get(scope: str, idem_key: str) -> dict | None:
    if not flags().idempotency:
        return None
    raw = await _redis().get(_cache_key(scope, idem_key))
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


async def idempotency_put(scope: str, idem_key: str, payload: dict) -> None:
    if not flags().idempotency:
        return
    f = flags()
    await _redis().set(
        _cache_key(scope, idem_key),
        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        ex=f.idempotency_ttl_sec,
    )


def idempotent(scope: str | None = None):
    """
    Декоратор POST/PUT хендлера. При повторном Idempotency-Key возвращает сохранённый JSON.

        @app.post("/users")
        @idempotent("users.create")
        async def create_user(request: Request, ...):
            ...
    """
    from python.libs.infra._wrap import preserve_signature

    def decorator(fn: Callable):
        async def wrapper(*args, **kwargs):
            f = flags()
            if not f.idempotency:
                return await fn(*args, **kwargs)

            request: Request | None = kwargs.get("request")
            if request is None:
                for a in args:
                    if isinstance(a, Request):
                        request = a
                        break
            if request is None:
                return await fn(*args, **kwargs)

            idem_key = request.headers.get(f.idempotency_header)
            if not idem_key:
                return await fn(*args, **kwargs)

            sc = scope or f"{request.method}:{request.url.path}"
            cached = await idempotency_get(sc, idem_key)
            if cached is not None:
                return JSONResponse(content=cached.get("body"), status_code=cached.get("status_code", 200))

            result = await fn(*args, **kwargs)

            if isinstance(result, JSONResponse):
                try:
                    body = json.loads(result.body.decode("utf-8"))
                except Exception:
                    return result
                await idempotency_put(sc, idem_key, {"status_code": result.status_code, "body": body})
            elif isinstance(result, (dict, list)):
                await idempotency_put(sc, idem_key, {"status_code": 200, "body": result})

            return result

        return preserve_signature(wrapper, fn)

    return decorator


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Глобальный middleware для методов записи.
    Работает прозрачно с любым JSON-ответом; декоратор @idempotent — точечно.
    Здесь middleware только помечает request.state — основная логика в декораторе,
    чтобы не буферизовать все ответы.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        f = flags()
        if f.idempotency:
            request.state.idempotency_key = request.headers.get(f.idempotency_header)
        return await call_next(request)
