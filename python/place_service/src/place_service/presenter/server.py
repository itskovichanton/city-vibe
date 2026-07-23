"""HTTP-сервер place-service: cities, categories, attr-schemas, places."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Query, Request
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

from python.libs.entities.place import PlaceCategory
from python.libs.infra import CityVibeInfraSupport
from python.libs.infra.decorators import rate_limit
from python.place_service.src.place_service.entities.search import PlaceSearchRequest
from python.place_service.src.place_service.infra.attrs_validation import validate_attrs
from python.place_service.src.place_service.infra.orm.mappers import city_dto_to_response, place_to_api_dict
from python.place_service.src.place_service.repo.attr_schema import AttrSchemaRepo
from python.place_service.src.place_service.repo.category import CategoryRepo
from python.place_service.src.place_service.repo.city import CityRepo
from python.place_service.src.place_service.repo.place import PlaceRepo
from python.place_service.src.place_service.repo.place_search import PlaceSearchRepo


class GeoIn(BaseModel):
    latitude: float
    longitude: float


class PlaceCreateBody(BaseModel):
    name: str
    about: str
    category: str = Field(..., description="Код категории (PlaceCategory)")
    owner_id: int
    geo: GeoIn
    attrs: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: List[Dict[str, Any]] = Field(default_factory=list)


class PlacePatchBody(BaseModel):
    name: Optional[str] = None
    about: Optional[str] = None
    category: Optional[str] = None
    geo: Optional[GeoIn] = None
    attrs: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: Optional[List[Dict[str, Any]]] = None


@bean(port=("server.port", int, 8083), host=("server.host", str, "0.0.0.0"))
class Server:
    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    city_repo: CityRepo
    category_repo: CategoryRepo
    attr_schema_repo: AttrSchemaRepo
    place_repo: PlaceRepo
    place_search_repo: PlaceSearchRepo
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
            title="City Vibe — Place Service",
            description="Города, категории, attrs-схемы, места на карте",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )
        self.error_handler_fast_api_support.mount(app)
        self.infra_support.mount(app)
        return app

    async def _resolve_and_validate_attrs(self, category_code: str, attrs: dict[str, Any] | None) -> dict:
        try:
            PlaceCategory(category_code)
        except ValueError as e:
            raise CoreException(message=f"Неизвестная категория: {category_code}") from e
        cat = await self.category_repo.get_by_code(category_code)
        if cat is None:
            raise CoreException(message=f"Категория {category_code} не найдена в справочнике")
        schema = await self.attr_schema_repo.get_by_category(category_code)
        if schema is None:
            raise CoreException(message=f"JSON Schema для категории {category_code} не найдена")
        return validate_attrs(attrs, schema.json_schema)

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            return self.presenter.present(
                Result(result={"status": "ok", "service": "place-service"}),
            )

        @self.fast_api.get("/cities", tags=["cities"], summary="Список крупных городов")
        @rate_limit("cities.list", limit=120)
        async def list_cities(request: Request):
            async def _list(_):
                cities = await self.city_repo.list_major()
                return [city_dto_to_response(c) for c in cities]

            return self.presenter.present(await self.action_runner.run(_list, call=None))

        @self.fast_api.get("/cities/{city_id}", tags=["cities"], summary="Город по id")
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

        @self.fast_api.get("/categories", tags=["categories"], summary="Справочник категорий мест")
        @rate_limit("categories.list", limit=120)
        async def list_categories(request: Request):
            async def _list(_):
                items = await self.category_repo.list_active()
                return [
                    {
                        "id": c.id,
                        "code": c.code,
                        "title": c.title,
                        "title_en": c.title_en,
                        "icon_url": c.icon_url,
                        "sort_order": c.sort_order,
                        "is_active": c.is_active,
                    }
                    for c in items
                ]

            return self.presenter.present(await self.action_runner.run(_list, call=None))

        @self.fast_api.get("/attr-schemas", tags=["attrs"], summary="Все JSON Schema attrs")
        @rate_limit("attr_schemas.list", limit=60)
        async def list_attr_schemas(request: Request):
            async def _list(_):
                items = await self.attr_schema_repo.list_all()
                return [
                    {
                        "id": s.id,
                        "category_code": s.category_code,
                        "version": s.version,
                        "json_schema": s.json_schema,
                    }
                    for s in items
                ]

            return self.presenter.present(await self.action_runner.run(_list, call=None))

        @self.fast_api.get(
            "/attr-schemas/{category_code}",
            tags=["attrs"],
            summary="JSON Schema attrs по категории",
        )
        @rate_limit("attr_schemas.get", limit=120)
        async def get_attr_schema(request: Request, category_code: str):
            async def _get(_):
                s = await self.attr_schema_repo.get_by_category(category_code)
                if s is None:
                    raise CoreException(
                        message=f"Schema для {category_code} не найдена",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return {
                    "id": s.id,
                    "category_code": s.category_code,
                    "version": s.version,
                    "json_schema": s.json_schema,
                }

            return self.presenter.present(await self.action_runner.run(_get, call=None))

        @self.fast_api.post("/places", tags=["places"], summary="Создать место")
        @rate_limit("places.create", limit=30)
        async def create_place(request: Request, body: PlaceCreateBody):
            async def _create(_):
                attrs = await self._resolve_and_validate_attrs(body.category, body.attrs)
                place = await self.place_repo.create(
                    name=body.name,
                    about=body.about,
                    category_code=body.category,
                    owner_id=body.owner_id,
                    lat=body.geo.latitude,
                    lng=body.geo.longitude,
                    attrs=attrs,
                    schedule=body.schedule,
                    pin_style_id=body.pin_style_id,
                    chat_theme_id=body.chat_theme_id,
                    city_id=body.city_id,
                    contacts=body.contacts,
                )
                return place_to_api_dict(place)

            return self.presenter.present(await self.action_runner.run(_create, call=None))

        @self.fast_api.get("/places", tags=["places"], summary="Список мест (фильтры)")
        @rate_limit("places.list", limit=120)
        async def list_places(
            request: Request,
            owner_id: Optional[int] = Query(None, description="Фильтр «мои места»"),
            category: Optional[str] = Query(None),
            min_lat: Optional[float] = Query(None),
            min_lng: Optional[float] = Query(None),
            max_lat: Optional[float] = Query(None),
            max_lng: Optional[float] = Query(None),
            limit: int = Query(100, ge=1, le=500),
        ):
            async def _list(_):
                bbox = None
                if None not in (min_lat, min_lng, max_lat, max_lng):
                    bbox = (min_lat, min_lng, max_lat, max_lng)
                places = await self.place_repo.list(
                    owner_id=owner_id, category=category, bbox=bbox, limit=limit
                )
                return [place_to_api_dict(p) for p in places]

            return self.presenter.present(await self.action_runner.run(_list, call=None))

        @self.fast_api.post(
            "/places/search",
            tags=["places", "search"],
            summary="Многокритериальный поиск мест",
            description=(
                "Гибкий поиск по city_id + category с фильтрами name / open_at / attrs "
                "(exact|between|or|and) и сортировкой rating|distance. "
                "Предназначен для мобильного клиента и вызова ИИ-агентом."
            ),
        )
        @rate_limit("places.search", limit=60)
        async def search_places(request: Request, body: PlaceSearchRequest):
            async def _search(_):
                # category уже в справочнике?
                cat = await self.category_repo.get_by_code(body.category)
                if cat is None:
                    raise CoreException(message=f"Категория {body.category} не найдена в справочнике")
                city = await self.city_repo.get_by_id(body.city_id)
                if city is None:
                    raise CoreException(
                        message=f"Город id={body.city_id} не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                # ключи attrs должны существовать в schema категории (мягко: неизвестные — ошибка)
                if body.attrs:
                    schema = await self.attr_schema_repo.get_by_category(body.category)
                    if schema is None:
                        raise CoreException(message=f"JSON Schema для {body.category} не найдена")
                    allowed = set((schema.json_schema.get("properties") or {}).keys())
                    unknown = [k for k in body.attrs if k not in allowed]
                    if unknown:
                        raise CoreException(
                            message=f"Неизвестные поля attrs для {body.category}: {', '.join(unknown)}"
                        )
                result = await self.place_search_repo.search(body)
                items = []
                for p in result.items:
                    d = place_to_api_dict(p)
                    if p.id in result.distances_m:
                        d["distance_m"] = round(result.distances_m[p.id], 1)
                    items.append(d)
                return {
                    "items": items,
                    "total": result.total,
                    "page": result.page,
                    "limit": result.limit,
                    "pages": (result.total + result.limit - 1) // result.limit if result.limit else 0,
                }

            return self.presenter.present(await self.action_runner.run(_search, call=None))

        @self.fast_api.get("/places/{place_id}", tags=["places"], summary="Место по id")
        @rate_limit("places.get", limit=120)
        async def get_place(request: Request, place_id: int):
            async def _get(_):
                place = await self.place_repo.get_by_id(place_id)
                if place is None:
                    raise CoreException(
                        message=f"Место id={place_id} не найдено",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return place_to_api_dict(place)

            return self.presenter.present(await self.action_runner.run(_get, call=None))

        @self.fast_api.patch("/places/{place_id}", tags=["places"], summary="Обновить место")
        @rate_limit("places.patch", limit=60)
        async def patch_place(request: Request, place_id: int, body: PlacePatchBody):
            async def _patch(_):
                existing = await self.place_repo.get_by_id(place_id)
                if existing is None:
                    raise CoreException(
                        message=f"Место id={place_id} не найдено",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                updates: dict[str, Any] = {}
                if body.name is not None:
                    updates["name"] = body.name
                if body.about is not None:
                    updates["about"] = body.about
                category_code = body.category or existing.category.value
                if body.category is not None:
                    updates["category_code"] = body.category
                if body.geo is not None:
                    updates["lat"] = body.geo.latitude
                    updates["lng"] = body.geo.longitude
                if body.attrs is not None or body.category is not None:
                    attrs_src = body.attrs if body.attrs is not None else existing.attrs
                    updates["attrs"] = await self._resolve_and_validate_attrs(category_code, attrs_src)
                if body.schedule is not None:
                    updates["schedule"] = body.schedule
                # pydantic v1 uses __fields_set__
                fields_set = getattr(body, "__fields_set__", None) or getattr(body, "model_fields_set", set())
                if "pin_style_id" in fields_set:
                    updates["pin_style_id"] = body.pin_style_id
                if "chat_theme_id" in fields_set:
                    updates["chat_theme_id"] = body.chat_theme_id
                if "city_id" in fields_set:
                    updates["city_id"] = body.city_id
                if body.contacts is not None:
                    updates["contacts"] = body.contacts
                place = await self.place_repo.update(place_id, **updates)
                return place_to_api_dict(place)

            return self.presenter.present(await self.action_runner.run(_patch, call=None))

        @self.fast_api.delete("/places/{place_id}", tags=["places"], summary="Soft-delete места")
        @rate_limit("places.delete", limit=30)
        async def delete_place(request: Request, place_id: int):
            async def _del(_):
                ok = await self.place_repo.soft_delete(place_id)
                if not ok:
                    raise CoreException(
                        message=f"Место id={place_id} не найдено",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return {"ok": True, "place_id": place_id}

            return self.presenter.present(await self.action_runner.run(_del, call=None))
