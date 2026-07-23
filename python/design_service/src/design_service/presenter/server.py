"""HTTP-сервер design-service."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Request
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.error_handler import ErrorHandlerFastAPISupport
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)
from src.mybootstrap_mvc_itskovichanton.pipeline import ActionRunner, Result
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from python.design_service.src.design_service.infra.orm.mappers import pin_to_api, theme_to_api
from python.design_service.src.design_service.repo.chat_theme import ChatThemeRepo
from python.design_service.src.design_service.repo.pin_style import PinStyleRepo
from python.libs.infra import CityVibeInfraSupport
from python.libs.infra.decorators import rate_limit


@bean(port=("server.port", int, 8085), host=("server.host", str, "0.0.0.0"))
class Server:
    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    pin_style_repo: PinStyleRepo
    chat_theme_repo: ChatThemeRepo
    presenter: ResultPresenter = default_dataclass_field(
        JSONResultPresenterImpl(exclude_unset=True),
    )

    def init(self, **kwargs):
        self.port = kwargs.get("port", getattr(self, "port", 8085))
        self.host = kwargs.get("host", getattr(self, "host", "0.0.0.0"))
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        app = FastAPI(
            title="City Vibe — Design Service",
            description="Дизайны пинов карты и тем чатов (медиа в S3)",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )
        self.error_handler_fast_api_support.mount(app)
        self.infra_support.mount(app)
        return app

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            return self.presenter.present(
                Result(result={"status": "ok", "service": "design-service"}),
            )

        @self.fast_api.get("/pin-styles", tags=["pins"], summary="Список стилей пинов")
        @rate_limit("pins.list", limit=120)
        async def list_pins(request: Request):
            async def _list(_):
                return [pin_to_api(p) for p in await self.pin_style_repo.list_all()]

            return self.presenter.present(await self.action_runner.run(_list, call=None))

        @self.fast_api.get("/pin-styles/default", tags=["pins"], summary="Стиль пина default")
        @rate_limit("pins.default", limit=120)
        async def default_pin(request: Request):
            async def _get(_):
                p = await self.pin_style_repo.get_by_code("default")
                if p is None:
                    raise CoreException(
                        message="default pin style не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return pin_to_api(p)

            return self.presenter.present(await self.action_runner.run(_get, call=None))

        @self.fast_api.get("/pin-styles/{style_id}", tags=["pins"], summary="Пин по id")
        @rate_limit("pins.get", limit=120)
        async def get_pin(request: Request, style_id: int):
            async def _get(_):
                p = await self.pin_style_repo.get_by_id(style_id)
                if p is None:
                    raise CoreException(
                        message=f"Pin style id={style_id} не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return pin_to_api(p)

            return self.presenter.present(await self.action_runner.run(_get, call=None))

        @self.fast_api.get("/chat-themes", tags=["themes"], summary="Список тем чата")
        @rate_limit("themes.list", limit=120)
        async def list_themes(request: Request):
            async def _list(_):
                return [theme_to_api(t) for t in await self.chat_theme_repo.list_all()]

            return self.presenter.present(await self.action_runner.run(_list, call=None))

        @self.fast_api.get("/chat-themes/default", tags=["themes"], summary="Тема чата default")
        @rate_limit("themes.default", limit=120)
        async def default_theme(request: Request):
            async def _get(_):
                t = await self.chat_theme_repo.get_by_code("default")
                if t is None:
                    raise CoreException(
                        message="default chat theme не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return theme_to_api(t)

            return self.presenter.present(await self.action_runner.run(_get, call=None))

        @self.fast_api.get("/chat-themes/{theme_id}", tags=["themes"], summary="Тема чата по id")
        @rate_limit("themes.get", limit=120)
        async def get_theme(request: Request, theme_id: int):
            async def _get(_):
                t = await self.chat_theme_repo.get_by_id(theme_id)
                if t is None:
                    raise CoreException(
                        message=f"Chat theme id={theme_id} не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return theme_to_api(t)

            return self.presenter.present(await self.action_runner.run(_get, call=None))
