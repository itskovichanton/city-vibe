"""
Rate limit (Redis fixed-window).

ENV: CITYVIBE_RATE_LIMIT_ENABLED=true
"""

from __future__ import annotations

import functools
from typing import Callable

from fastapi import Request
from src.mybootstrap_core_itskovichanton.di import injector
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_TOO_MANY_REQUESTS,
    CoreException,
)

from python.libs.infra.flags import flags
from python.libs.infra.redis_client import RedisClient


def _client_key(request: Request | None, bucket: str) -> str:
    ip = "anon"
    if request is not None:
        ip = request.client.host if request.client else "anon"
        # S2S / user identity если есть
        tok = request.headers.get(flags().s2s_header)
        if tok:
            ip = f"svc:{tok[:8]}"
    return f"cityvibe:rl:{bucket}:{ip}"


def rate_limit(bucket: str, limit: int | None = None, window_sec: int | None = None):
    """
        @app.post("/users/{id}/avatar")
        @rate_limit("avatar", limit=10, window_sec=60)
        async def upload_avatar(request: Request, ...):
    """
    from python.libs.infra._wrap import preserve_signature

    def decorator(fn: Callable):
        async def wrapper(*args, **kwargs):
            f = flags()
            if not f.rate_limit:
                return await fn(*args, **kwargs)

            request: Request | None = kwargs.get("request")
            if request is None:
                for a in args:
                    if isinstance(a, Request):
                        request = a
                        break

            lim = limit if limit is not None else f.rate_limit_default
            win = window_sec if window_sec is not None else f.rate_limit_window_sec
            key = _client_key(request, bucket)

            redis = injector().inject(RedisClient)
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, win)
            if count > lim:
                raise CoreException(
                    message=f"Rate limit exceeded for '{bucket}' ({lim}/{win}s)",
                    reason=ERR_REASON_TOO_MANY_REQUESTS,
                )
            return await fn(*args, **kwargs)

        return preserve_signature(wrapper, fn)

    return decorator
