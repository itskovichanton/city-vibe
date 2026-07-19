"""Request-ID middleware: прокидывает X-Request-ID в contextvars и ответ."""

from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from python.libs.infra.context import set_request_id
from python.libs.infra.flags import env_str, flags

HEADER = env_str("CITYVIBE_REQUEST_ID_HEADER", "X-Request-ID")


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = HEADER):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next) -> Response:
        if not flags().request_id:
            return await call_next(request)

        rid = request.headers.get(self.header_name) or str(uuid4())
        set_request_id(rid)
        request.state.request_id = rid
        response = await call_next(request)
        response.headers[self.header_name] = rid
        return response
