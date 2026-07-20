"""HTTP-сервер place-catalog."""

from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
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
from python.place_catalog.src.place_catalog.infra.orm.mappers import city_dto_to_response
from python.place_catalog.src.place_catalog.repo.city import CityRepo


class CityOut(BaseModel):
    id: int
    name: str
    slug: str
    region: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_major: bool = True
    sort_order: int = 0
    about: str = ""


@bean(port=("server.port", int, 8083), host=("server.host", str, "0.0.0.0"))
class Server:
    """FastAPI-сервер справочника городов."""

    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    city_repo: CityRepo
    presenter: ResultPresenter = default_dataclass_field(
        JSONResultPresenterImpl(exclude_unset=True),
    )

    def init(self, **kwargs):
        self.port = kwargs.get("port", getattr(self, "port", 8083))
        self.host = kwargs.get("host", getattr(self, "host", "0.0.0.0"))
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        app = FastAPI(
            title="City Vibe — Place Catalog",
            description="Справочник городов",
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
                Result(result={"status": "ok", "service": "place-catalog"}),
            )

        @self.fast_api.get("/cities", tags=["cities"], response_model=List[CityOut], summary="Список крупных городов")
        @rate_limit("cities.list", limit=120)
        async def list_cities(request: Request):
            async def _list(_):
                cities = await self.city_repo.list_major()
                return [city_dto_to_response(c) for c in cities]

            return self.presenter.present(await self.action_runner.run(_list, call=None))

        @self.fast_api.get("/cities/{city_id}", tags=["cities"], response_model=CityOut, summary="Город по id")
        @rate_limit("cities.get", limit=120)
        async def get_city(request: Request, city_id: int):
            async def _get(_):
                city = await self.city_repo.get_by_id(city_id)
                if city is None:
                    raise CoreException(
                        message=f"Город id={city_id} не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return city_dto_to_response(city)

            return self.presenter.present(await self.action_runner.run(_get, call=None))
