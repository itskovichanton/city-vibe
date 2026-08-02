"""HTTP-сервер milana-service."""

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

from python.libs.infra import CityVibeInfraSupport
from python.libs.infra.decorators import rate_limit
from python.milana_service.src.milana_service.agent.places_nl_search import PlacesNlSearchAgent
from python.milana_service.src.milana_service.entities.request import MilanaPlacesSearchRequest
from python.milana_service.src.milana_service.usecase.get_milana_account import GetMilanaAccountUseCase


@bean(port=("server.port", int, 8086), host=("server.host", str, "0.0.0.0"))
class Server:
    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    places_nl_agent: PlacesNlSearchAgent
    get_milana_account_uc: GetMilanaAccountUseCase
    presenter: ResultPresenter = default_dataclass_field(
        JSONResultPresenterImpl(exclude_unset=True),
    )

    def init(self, **kwargs):
        self.port = kwargs.get("port", getattr(self, "port", 8086))
        self.host = kwargs.get("host", getattr(self, "host", "0.0.0.0"))
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        app = FastAPI(
            title="City Vibe — Milana Service",
            description="ИИ-агент Милана: NL → places/search (DeepSeek, variant B)",
            version="1.1.0",
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
                Result(
                    result={
                        "status": "ok",
                        "service": "milana-service",
                        "deepseek_configured": self.places_nl_agent.deepseek.configured,
                    }
                ),
            )

        @self.fast_api.get(
            "/milana/account",
            tags=["milana", "account"],
            summary="Публичный профиль служебного аккаунта Миланы",
        )
        @rate_limit("milana.account", limit=120)
        async def milana_account(request: Request):
            return self.presenter.present(
                await self.action_runner.run(self.get_milana_account_uc.execute, call=None),
            )

        @self.fast_api.get(
            "/milana/world",
            tags=["milana", "world"],
            summary="Справочник мира для Миланы (города + категории)",
        )
        @rate_limit("milana.world", limit=60)
        async def milana_world(request: Request):
            async def _run(_):
                return await self.places_nl_agent.world_digest()

            return self.presenter.present(await self.action_runner.run(_run, call=None))

        @self.fast_api.get(
            "/milana/cities",
            tags=["milana", "world"],
            summary="Города (compact) для знакомства ИИ с миром",
        )
        @rate_limit("milana.cities", limit=60)
        async def milana_cities(request: Request):
            async def _run(_):
                return await self.places_nl_agent.places.list_cities_compact()

            return self.presenter.present(await self.action_runner.run(_run, call=None))

        @self.fast_api.get(
            "/milana/categories",
            tags=["milana", "world"],
            summary="Категории мест (compact) для знакомства ИИ с миром",
        )
        @rate_limit("milana.categories", limit=60)
        async def milana_categories(request: Request):
            async def _run(_):
                return await self.places_nl_agent.places.list_categories_compact()

            return self.presenter.present(await self.action_runner.run(_run, call=None))

        @self.fast_api.get(
            "/milana/attr-schemas/{category_code}",
            tags=["milana", "world"],
            summary="Compact JSON Schema attrs категории (для LLM)",
        )
        @rate_limit("milana.attr_schema", limit=120)
        async def milana_attr_schema(request: Request, category_code: str):
            async def _run(_):
                try:
                    return await self.places_nl_agent.places.get_attr_schema_compact(category_code)
                except CoreException:
                    raise
                except Exception as e:
                    raise CoreException(
                        message=f"Schema для {category_code} не найдена: {e}",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    ) from e

            return self.presenter.present(await self.action_runner.run(_run, call=None))

        @self.fast_api.post(
            "/milana/places/search",
            tags=["milana", "places"],
            summary="NL-поиск мест через ИИ-агента Милану (variant B)",
            description=(
                "q — произвольный русский текст. Милана: (1) план по справочникам мира, "
                "(2) сборка тел places/search по compact schema выбранных категорий, "
                "(3) исполнение search, (4) message от Миланы. Требует DEEPSEEK_API_KEY."
            ),
        )
        @rate_limit("milana.places.search", limit=20)
        async def milana_places_search(request: Request, body: MilanaPlacesSearchRequest):
            async def _run(_):
                result = await self.places_nl_agent.run(body)
                return result.model_dump()

            return self.presenter.present(await self.action_runner.run(_run, call=None))
