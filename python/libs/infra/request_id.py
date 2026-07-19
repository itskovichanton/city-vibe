"""
Request-ID через asgi-correlation-id.

ENV: CITYVIBE_REQUEST_ID_ENABLED=true
Header: CITYVIBE_REQUEST_ID_HEADER (default X-Request-ID)
"""

from __future__ import annotations

from asgi_correlation_id import CorrelationIdMiddleware

from python.libs.infra.flags import env_str

HEADER = env_str("CITYVIBE_REQUEST_ID_HEADER", "X-Request-ID")

__all__ = ["CorrelationIdMiddleware", "HEADER"]
