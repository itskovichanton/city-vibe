"""HTTP-сервер notification-service."""

import asyncio

import uvicorn
from fastapi import FastAPI
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.error_handler import ErrorHandlerFastAPISupport
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.pipeline import Result
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from python.libs.infra import CityVibeInfraSupport
from python.notification_service.src.notification_service.worker.notification_worker import NotificationWorker


@bean(port=("server.port", int, 8084), host=("server.host", str, "0.0.0.0"))
class Server:
    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    notification_worker: NotificationWorker
    presenter: ResultPresenter = default_dataclass_field(JSONResultPresenterImpl(exclude_unset=True))

    def init(self, **kwargs):
        self.port = kwargs.get("port", getattr(self, "port", 8084))
        self.host = kwargs.get("host", getattr(self, "host", "0.0.0.0"))
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        app = FastAPI(
            title="City Vibe — Notification Service",
            description="Email/SMS по событиям",
            version="1.0.0",
            docs_url="/docs",
            openapi_url="/openapi.json",
        )
        self.error_handler_fast_api_support.mount(app)
        self.infra_support.mount(app)

        @app.on_event("startup")
        async def _start_worker():
            # намеренно без await — фоновый consumer на весь lifetime процесса
            self._worker_task = asyncio.create_task(self.notification_worker.start())

        return app

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            return self.presenter.present(
                Result(result={"status": "ok", "service": "notification-service"}),
            )
