"""HTTP-клиент place-service."""

from __future__ import annotations

from typing import Any, Optional, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.client.http import on_mbclient_api

api_call = on_mbclient_api(_name="clients.place_service")


class PlaceServiceClient(Protocol):
    def health(self) -> Any: ...

    def list_cities(self) -> Any: ...

    def nearest_city(self, lat: float, lng: float) -> Any: ...

    def get_city(self, city_id: int) -> Any: ...

    def list_categories(self) -> Any: ...

    def list_attr_schemas(self) -> Any: ...

    def get_attr_schema(self, category_code: str) -> Any: ...

    def create_place(self, body: dict) -> Any: ...

    def list_places(
        self,
        owner_id: Optional[int] = None,
        category: Optional[str] = None,
        **kwargs,
    ) -> Any: ...

    def get_place(self, place_id: int) -> Any: ...

    def patch_place(self, place_id: int, body: dict) -> Any: ...

    def delete_place(self, place_id: int) -> Any: ...

    def search_places(self, body: dict) -> Any: ...

    def list_product_categories(self) -> Any: ...

    def create_product(self, body: dict) -> Any: ...

    def list_products(
        self,
        place_id: Optional[int] = None,
        category: Optional[str] = None,
        **kwargs,
    ) -> Any: ...

    def get_product(self, product_id: int) -> Any: ...

    def patch_product(self, product_id: int, body: dict) -> Any: ...

    def delete_product(self, product_id: int) -> Any: ...

    def search_products(self, body: dict) -> Any: ...


@bean
class PlaceServiceClientImpl(PlaceServiceClient):
    @api_call
    def health(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/health", timeout=30, headers=headers)

    @api_call
    def list_cities(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/cities", timeout=30, headers=headers)

    @api_call
    def nearest_city(self, lat: float, lng: float, session=None, url=None, headers=None):
        return session.get(
            url=f"{url}/cities/nearest",
            params={"lat": lat, "lng": lng},
            timeout=30,
            headers=headers,
        )

    @api_call
    def get_city(self, city_id: int, session=None, url=None, headers=None):
        return session.get(url=f"{url}/cities/{city_id}", timeout=30, headers=headers)

    @api_call
    def list_categories(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/categories", timeout=30, headers=headers)

    @api_call
    def list_attr_schemas(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/attr-schemas", timeout=30, headers=headers)

    @api_call
    def get_attr_schema(self, category_code: str, session=None, url=None, headers=None):
        return session.get(url=f"{url}/attr-schemas/{category_code}", timeout=30, headers=headers)

    @api_call
    def create_place(self, body: dict, session=None, url=None, headers=None):
        return session.post(url=f"{url}/places", json=body, timeout=30, headers=headers)

    @api_call
    def list_places(
        self,
        owner_id: Optional[int] = None,
        category: Optional[str] = None,
        session=None,
        url=None,
        headers=None,
        **kwargs,
    ):
        params = {}
        if owner_id is not None:
            params["owner_id"] = owner_id
        if category is not None:
            params["category"] = category
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return session.get(url=f"{url}/places", params=params, timeout=30, headers=headers)

    @api_call
    def get_place(self, place_id: int, session=None, url=None, headers=None):
        return session.get(url=f"{url}/places/{place_id}", timeout=30, headers=headers)

    @api_call
    def patch_place(self, place_id: int, body: dict, session=None, url=None, headers=None):
        return session.patch(url=f"{url}/places/{place_id}", json=body, timeout=30, headers=headers)

    @api_call
    def delete_place(self, place_id: int, session=None, url=None, headers=None):
        return session.delete(url=f"{url}/places/{place_id}", timeout=30, headers=headers)

    @api_call
    def search_places(self, body: dict, session=None, url=None, headers=None):
        return session.post(url=f"{url}/places/search", json=body, timeout=60, headers=headers)

    @api_call
    def list_product_categories(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/product-categories", timeout=30, headers=headers)

    @api_call
    def create_product(self, body: dict, session=None, url=None, headers=None):
        return session.post(url=f"{url}/products", json=body, timeout=30, headers=headers)

    @api_call
    def list_products(
        self,
        place_id: Optional[int] = None,
        category: Optional[str] = None,
        session=None,
        url=None,
        headers=None,
        **kwargs,
    ):
        params = {}
        if place_id is not None:
            params["place_id"] = place_id
        if category is not None:
            params["category"] = category
        params.update({k: v for k, v in kwargs.items() if v is not None})
        return session.get(url=f"{url}/products", params=params, timeout=30, headers=headers)

    @api_call
    def get_product(self, product_id: int, session=None, url=None, headers=None):
        return session.get(url=f"{url}/products/{product_id}", timeout=30, headers=headers)

    @api_call
    def patch_product(self, product_id: int, body: dict, session=None, url=None, headers=None):
        return session.patch(url=f"{url}/products/{product_id}", json=body, timeout=30, headers=headers)

    @api_call
    def delete_product(self, product_id: int, session=None, url=None, headers=None):
        return session.delete(url=f"{url}/products/{product_id}", timeout=30, headers=headers)

    @api_call
    def search_products(self, body: dict, session=None, url=None, headers=None):
        return session.post(url=f"{url}/products/search", json=body, timeout=60, headers=headers)
