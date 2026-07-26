"""Подробный HTTP access-лог в файл (LoggerService.get_file_logger('http'))."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from python.libs.infra.context import get_request_id, get_service_name


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _client_ip(request: Request) -> str | None:
    if "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _headers_dict(headers) -> dict[str, str]:
    return {k: v for k, v in headers.items()}


def _query_params(request: Request) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, value in request.query_params.multi_items():
        if key in params:
            cur = params[key]
            if isinstance(cur, list):
                cur.append(value)
            else:
                params[key] = [cur, value]
        else:
            params[key] = value
    return params


def _decode_body(raw: bytes, *, content_type: str, max_bytes: int) -> Any:
    if not raw:
        return None
    truncated = len(raw) > max_bytes
    data = raw[:max_bytes]
    ctype = (content_type or "").lower()
    if any(x in ctype for x in ("multipart/", "octet-stream", "image/", "audio/", "video/", "zip")):
        return {"encoding": "binary", "content_type": content_type, "size": len(raw), "truncated": truncated}
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"encoding": "binary", "content_type": content_type, "size": len(raw), "truncated": truncated}
    # непечатные → binary summary
    if text and sum(1 for ch in text if ord(ch) < 9 or (13 < ord(ch) < 32)) / max(len(text), 1) > 0.3:
        return {"encoding": "binary", "content_type": content_type, "size": len(raw), "truncated": truncated}
    if "json" in ctype:
        try:
            parsed = json.loads(text)
            if truncated:
                return {"encoding": "json", "truncated": True, "size": len(raw), "preview": parsed}
            return parsed
        except json.JSONDecodeError:
            pass
    out: Any = text
    if truncated:
        out = {"encoding": "text", "truncated": True, "size": len(raw), "preview": text}
    return out


async def _read_request_body(request: Request, max_bytes: int) -> Any:
    if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        return None
    try:
        raw = await request.body()
    except Exception as exc:
        return {"error": f"read_request_body: {exc}"}
    return _decode_body(raw, content_type=request.headers.get("content-type", ""), max_bytes=max_bytes)


async def _read_response_body(response: Response, max_bytes: int) -> Any:
    try:
        chunks: list[bytes] = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            chunks.append(chunk)
        raw = b"".join(chunks)

        async def _replay():
            yield raw

        response.body_iterator = _replay()
        # content-length мог сбиться после перечитывания — оставляем как есть
        return _decode_body(
            raw,
            content_type=response.headers.get("content-type", ""),
            max_bytes=max_bytes,
        )
    except Exception as exc:
        return {"error": f"read_response_body: {exc}"}


class DetailedHTTPLoggingMiddleware(BaseHTTPMiddleware):
    """
    Максимально подробный HTTP-лог в файл:
    method, url, path, query, headers, bodies, status, timing, request_id, client.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        logger: logging.Logger,
        max_body_bytes: int = 1_048_576,
        log_request_body: bool = True,
        log_response_body: bool = True,
        excluded_paths: Optional[set[str]] = None,
    ):
        super().__init__(app)
        self.logger = logger
        self.max_body_bytes = max(1024, int(max_body_bytes))
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.excluded_paths = excluded_paths or set()

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        if path in self.excluded_paths:
            return await call_next(request)

        started = time.perf_counter()
        req_body = await _read_request_body(request, self.max_body_bytes) if self.log_request_body else None

        error: str | None = None
        response: Response | None = None
        try:
            response = await call_next(request)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            status = getattr(response, "status_code", None) if response is not None else None
            resp_body = None
            resp_headers: dict[str, str] = {}
            if response is not None:
                resp_headers = _headers_dict(response.headers)
                if self.log_response_body:
                    resp_body = await _read_response_body(response, self.max_body_bytes)

            rid = get_request_id() or request.headers.get("x-request-id")
            if response is not None and not rid:
                rid = response.headers.get("x-request-id")

            entry = {
                "t": _utc_now(),
                "kind": "http",
                "service": get_service_name() or self.logger.name,
                "request_id": rid,
                "method": request.method,
                "path": path,
                "url": str(request.url),
                "query": _query_params(request),
                "client": {
                    "ip": _client_ip(request),
                    "port": request.client.port if request.client else None,
                },
                "request": {
                    "headers": _headers_dict(request.headers),
                    "body": req_body,
                },
                "response": {
                    "status": status,
                    "headers": resp_headers,
                    "body": resp_body,
                    "elapsed_ms": elapsed_ms,
                },
                "error": error,
            }
            try:
                self.logger.info(entry)
            except Exception:
                logging.getLogger(__name__).exception("HTTP file log write failed")

        assert response is not None
        return response
