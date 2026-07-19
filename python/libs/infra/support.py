"""
Единая точка подключения инфраструктурных middleware к FastAPI.

    infra_support: CityVibeInfraSupport
    ...
    self.infra_support.mount(app)
"""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from fastapi import FastAPI
from src.mybootstrap_core_itskovichanton.di import injector
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.infra.flags import flags
from python.libs.infra.idempotency import IdempotencyMiddleware
from python.libs.infra.outbox import Outbox, OutboxImpl
from python.libs.infra.request_id import HEADER, CorrelationIdMiddleware
from python.libs.infra.s2s import S2SAuthMiddleware
from python.libs.infra.tracing import instrument_fastapi, instrument_requests, setup_tracer_provider

logger = logging.getLogger(__name__)


@bean
class CityVibeInfraSupport:
    """Вешает middleware согласно ENV-флагам. Вызывать один раз при создании FastAPI."""

    def mount(self, app: FastAPI) -> None:
        f = flags()
        # Порядок: последний add_middleware = самый внешний.
        if f.idempotency:
            app.add_middleware(IdempotencyMiddleware)
            logger.info("Infra: IdempotencyMiddleware ON")
        if f.s2s_auth:
            app.add_middleware(S2SAuthMiddleware)
            logger.info("Infra: S2SAuthMiddleware ON")
        if f.request_id:
            # validator=None — принимаем любой непустой X-Request-ID (не только UUID4)
            app.add_middleware(
                CorrelationIdMiddleware,
                header_name=HEADER,
                generator=lambda: str(uuid4()),
                validator=None,
            )
            logger.info("Infra: CorrelationIdMiddleware ON (%s)", HEADER)

        if f.tracing:
            setup_tracer_provider()
            instrument_fastapi(app)
            instrument_requests()

        @app.on_event("startup")
        async def _start_outbox_relay():
            if not flags().outbox:
                return
            outbox = injector().inject(Outbox)
            if isinstance(outbox, OutboxImpl):

                async def _loop():
                    logger.info("Outbox relay started (poll=%ss)", flags().outbox_poll_sec)
                    while True:
                        try:
                            n = await outbox.flush_once()
                            if n:
                                logger.info("Outbox: опубликовано %s", n)
                        except Exception:
                            logger.exception("Outbox relay error")
                        await asyncio.sleep(flags().outbox_poll_sec)

                asyncio.create_task(_loop())

        logger.info(
            "Infra flags: request_id=%s s2s=%s idempotency=%s rate_limit=%s upload=%s outbox=%s tracing=%s",
            f.request_id,
            f.s2s_auth,
            f.idempotency,
            f.rate_limit,
            f.upload_validation,
            f.outbox,
            f.tracing,
        )
