"""HTTP-сервер place-service: cities, categories, attr-schemas, places."""

from __future__ import annotations

from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, Request
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.error_handler import ErrorHandlerFastAPISupport
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.pipeline import ActionRunner, Result
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from python.libs.infra import CityVibeInfraSupport
from python.libs.infra.decorators import rate_limit
from python.place_service.src.place_service.entities.search import PlaceSearchRequest, ProductSearchRequest
from python.place_service.src.place_service.presenter.mappers import (
    to_create_place_request,
    to_create_product_request,
    to_delete_place_request,
    to_delete_product_request,
    to_get_attr_schema_request,
    to_list_places_request,
    to_list_products_request,
    to_nearest_city_request,
    to_patch_place_request,
    to_patch_product_request,
)
from python.place_service.src.place_service.presenter.models import (
    PlaceCreateBody,
    PlacePatchBody,
    ProductCreateBody,
    ProductPatchBody,
)
from python.place_service.src.place_service.usecase.attr_schemas import (
    GetAttrSchemaUseCase,
    ListAttrSchemasUseCase,
)
from python.place_service.src.place_service.usecase.categories import ListCategoriesUseCase
from python.place_service.src.place_service.usecase.cities import (
    GetCityUseCase,
    GetNearestCityUseCase,
    ListCitiesUseCase,
)
from python.place_service.src.place_service.usecase.places import (
    CreatePlaceUseCase,
    DeletePlaceUseCase,
    GetPlaceUseCase,
    ListPlacesUseCase,
    PatchPlaceUseCase,
)
from python.place_service.src.place_service.usecase.product_categories import ListProductCategoriesUseCase
from python.place_service.src.place_service.usecase.products import (
    CreateProductUseCase,
    DeleteProductUseCase,
    GetProductUseCase,
    ListProductsUseCase,
    PatchProductUseCase,
)
from python.place_service.src.place_service.usecase.search_places import SearchPlacesUseCase
from python.place_service.src.place_service.usecase.search_products import SearchProductsUseCase


@bean(port=("server.port", int, 8083), host=("server.host", str, "0.0.0.0"))
class Server:
    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    list_cities_uc: ListCitiesUseCase
    get_nearest_city_uc: GetNearestCityUseCase
    get_city_uc: GetCityUseCase
    list_categories_uc: ListCategoriesUseCase
    list_attr_schemas_uc: ListAttrSchemasUseCase
    get_attr_schema_uc: GetAttrSchemaUseCase
    create_place_uc: CreatePlaceUseCase
    list_places_uc: ListPlacesUseCase
    search_places_uc: SearchPlacesUseCase
    get_place_uc: GetPlaceUseCase
    patch_place_uc: PatchPlaceUseCase
    delete_place_uc: DeletePlaceUseCase
    list_product_categories_uc: ListProductCategoriesUseCase
    create_product_uc: CreateProductUseCase
    list_products_uc: ListProductsUseCase
    search_products_uc: SearchProductsUseCase
    get_product_uc: GetProductUseCase
    patch_product_uc: PatchProductUseCase
    delete_product_uc: DeleteProductUseCase
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
            description="Города, категории, attrs-схемы, места и продукты",
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
                Result(result={"status": "ok", "service": "place-service"}),
            )

        @self.fast_api.get("/cities", tags=["cities"], summary="Список крупных городов")
        @rate_limit("cities.list", limit=120)
        async def list_cities(request: Request):
            return self.presenter.present(
                await self.action_runner.run(self.list_cities_uc.execute, call=None),
            )

        @self.fast_api.get(
            "/cities/nearest",
            tags=["cities"],
            summary="Ближайший крупный город к координатам",
        )
        @rate_limit("cities.nearest", limit=60)
        async def nearest_city(
            request: Request,
            lat: float = Query(..., description="Широта"),
            lng: float = Query(..., description="Долгота"),
        ):
            return self.presenter.present(
                await self.action_runner.run(
                    self.get_nearest_city_uc.execute,
                    call=to_nearest_city_request(lat, lng),
                ),
            )

        @self.fast_api.get("/cities/{city_id}", tags=["cities"], summary="Город по id")
        @rate_limit("cities.get", limit=120)
        async def get_city(request: Request, city_id: int):
            return self.presenter.present(
                await self.action_runner.run(self.get_city_uc.execute, call=city_id),
            )

        @self.fast_api.get("/categories", tags=["categories"], summary="Справочник категорий мест")
        @rate_limit("categories.list", limit=120)
        async def list_categories(request: Request):
            return self.presenter.present(
                await self.action_runner.run(self.list_categories_uc.execute, call=None),
            )

        @self.fast_api.get("/attr-schemas", tags=["attrs"], summary="Все JSON Schema attrs")
        @rate_limit("attr_schemas.list", limit=60)
        async def list_attr_schemas(request: Request):
            return self.presenter.present(
                await self.action_runner.run(self.list_attr_schemas_uc.execute, call=None),
            )

        @self.fast_api.get(
            "/attr-schemas/{category_code}",
            tags=["attrs"],
            summary="JSON Schema attrs по категории",
        )
        @rate_limit("attr_schemas.get", limit=120)
        async def get_attr_schema(
            request: Request,
            category_code: str,
            compact: bool = False,
        ):
            return self.presenter.present(
                await self.action_runner.run(
                    self.get_attr_schema_uc.execute,
                    call=to_get_attr_schema_request(category_code, compact=compact),
                ),
            )

        @self.fast_api.post("/places", tags=["places"], summary="Создать место")
        @rate_limit("places.create", limit=30)
        async def create_place(request: Request, body: PlaceCreateBody):
            return self.presenter.present(
                await self.action_runner.run(
                    self.create_place_uc.execute,
                    call=to_create_place_request(body),
                ),
            )

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
            return self.presenter.present(
                await self.action_runner.run(
                    self.list_places_uc.execute,
                    call=to_list_places_request(
                        owner_id=owner_id,
                        category=category,
                        min_lat=min_lat,
                        min_lng=min_lng,
                        max_lat=max_lat,
                        max_lng=max_lng,
                        limit=limit,
                    ),
                ),
            )

        @self.fast_api.post(
            "/places/search",
            tags=["places", "search"],
            summary="Многокритериальный поиск мест",
            description=(
                "Обязателен city_id; нужен якорь category / name / open_at. "
                "Опционально timezone, exclude_ids, sort_by=rating|distance|created_at, "
                "open_at, attrs. Для мобильного клиента и ИИ-агента."
            ),
        )
        @rate_limit("places.search", limit=60)
        async def search_places(request: Request, body: PlaceSearchRequest):
            return self.presenter.present(
                await self.action_runner.run(self.search_places_uc.execute, call=body),
            )

        @self.fast_api.get("/places/{place_id}", tags=["places"], summary="Место по id")
        @rate_limit("places.get", limit=120)
        async def get_place(request: Request, place_id: int):
            return self.presenter.present(
                await self.action_runner.run(self.get_place_uc.execute, call=place_id),
            )

        @self.fast_api.patch("/places/{place_id}", tags=["places"], summary="Обновить место")
        @rate_limit("places.patch", limit=60)
        async def patch_place(request: Request, place_id: int, body: PlacePatchBody):
            return self.presenter.present(
                await self.action_runner.run(
                    self.patch_place_uc.execute,
                    call=to_patch_place_request(place_id, body),
                ),
            )

        @self.fast_api.delete("/places/{place_id}", tags=["places"], summary="Soft-delete места")
        @rate_limit("places.delete", limit=30)
        async def delete_place(request: Request, place_id: int):
            return self.presenter.present(
                await self.action_runner.run(
                    self.delete_place_uc.execute,
                    call=to_delete_place_request(place_id),
                ),
            )

        @self.fast_api.get(
            "/product-categories",
            tags=["products"],
            summary="Справочник категорий товаров и услуг",
        )
        @rate_limit("product_categories.list", limit=120)
        async def list_product_categories(request: Request):
            return self.presenter.present(
                await self.action_runner.run(self.list_product_categories_uc.execute, call=None),
            )

        @self.fast_api.post("/products", tags=["products"], summary="Создать продукт")
        @rate_limit("products.create", limit=30)
        async def create_product(request: Request, body: ProductCreateBody):
            return self.presenter.present(
                await self.action_runner.run(
                    self.create_product_uc.execute,
                    call=to_create_product_request(body),
                ),
            )

        @self.fast_api.get("/products", tags=["products"], summary="Список продуктов")
        @rate_limit("products.list", limit=120)
        async def list_products(
            request: Request,
            place_id: Optional[int] = Query(None),
            category: Optional[str] = Query(None),
            limit: int = Query(100, ge=1, le=500),
        ):
            return self.presenter.present(
                await self.action_runner.run(
                    self.list_products_uc.execute,
                    call=to_list_products_request(
                        place_id=place_id,
                        category=category,
                        limit=limit,
                    ),
                ),
            )

        @self.fast_api.post(
            "/products/search",
            tags=["products", "search"],
            summary="Многокритериальный поиск продуктов",
            description=(
                "Обязателен city_id; якорь category / q / place_id / place_name / "
                "place_category / date_from. q ищет по продукту и имени места. "
                "exclude_ids vs exclude_place_ids, one_per_place, events, include_past=false, "
                "sort_by=price|distance|created_at|event_start (NULL price — NULLS LAST)."
            ),
        )
        @rate_limit("products.search", limit=60)
        async def search_products(request: Request, body: ProductSearchRequest):
            return self.presenter.present(
                await self.action_runner.run(self.search_products_uc.execute, call=body),
            )

        @self.fast_api.get("/products/{product_id}", tags=["products"], summary="Продукт по id")
        @rate_limit("products.get", limit=120)
        async def get_product(request: Request, product_id: int):
            return self.presenter.present(
                await self.action_runner.run(self.get_product_uc.execute, call=product_id),
            )

        @self.fast_api.patch("/products/{product_id}", tags=["products"], summary="Обновить продукт")
        @rate_limit("products.patch", limit=60)
        async def patch_product(request: Request, product_id: int, body: ProductPatchBody):
            return self.presenter.present(
                await self.action_runner.run(
                    self.patch_product_uc.execute,
                    call=to_patch_product_request(product_id, body),
                ),
            )

        @self.fast_api.delete("/products/{product_id}", tags=["products"], summary="Soft-delete продукта")
        @rate_limit("products.delete", limit=30)
        async def delete_product(request: Request, product_id: int):
            return self.presenter.present(
                await self.action_runner.run(
                    self.delete_product_uc.execute,
                    call=to_delete_product_request(product_id),
                ),
            )
