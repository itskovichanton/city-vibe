"""HTTP-клиент place-catalog (on_mbclient_api + requests)."""

from __future__ import annotations

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.client.http import on_mbclient_api

api_call = on_mbclient_api(_name="clients.place_catalog")


class PlaceCatalogClient(Protocol):
    def health(self) -> Any: ...

    def list_cities(self) -> Any: ...

    def get_city(self, city_id: int) -> Any: ...


@bean
class PlaceCatalogClientImpl(PlaceCatalogClient):
    @api_call
    def health(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/health", timeout=30, headers=headers)

    @api_call
    def list_cities(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/cities", timeout=30, headers=headers)

    @api_call
    def get_city(self, city_id: int, session=None, url=None, headers=None):
        return session.get(url=f"{url}/cities/{city_id}", timeout=30, headers=headers)
