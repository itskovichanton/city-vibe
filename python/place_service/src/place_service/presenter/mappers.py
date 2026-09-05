"""Маппинг HTTP → DTO use-case."""

from __future__ import annotations

from python.place_service.src.place_service.entities.common import (
    CreatePlaceRequest,
    CreateProductRequest,
    DeletePlaceRequest,
    DeleteProductRequest,
    GetAttrSchemaRequest,
    ListPlacesRequest,
    ListProductsRequest,
    NearestCityRequest,
    PatchPlaceRequest,
    PatchProductRequest,
)
from python.place_service.src.place_service.presenter.models import (
    PlaceCreateBody,
    PlacePatchBody,
    ProductCreateBody,
    ProductPatchBody,
)


def to_nearest_city_request(lat: float, lng: float) -> NearestCityRequest:
    return NearestCityRequest(lat=lat, lng=lng)


def to_get_attr_schema_request(category_code: str, *, compact: bool) -> GetAttrSchemaRequest:
    return GetAttrSchemaRequest(category_code=category_code, compact=compact)


def to_create_place_request(body: PlaceCreateBody) -> CreatePlaceRequest:
    return CreatePlaceRequest(
        name=body.name,
        about=body.about,
        category=body.category,
        owner_id=body.owner_id,
        lat=body.geo.latitude,
        lng=body.geo.longitude,
        attrs=body.attrs,
        schedule=body.schedule,
        pin_style_id=body.pin_style_id,
        chat_theme_id=body.chat_theme_id,
        city_id=body.city_id,
        contacts=body.contacts,
    )


def to_list_places_request(
    *,
    owner_id: int | None,
    category: str | None,
    min_lat: float | None,
    min_lng: float | None,
    max_lat: float | None,
    max_lng: float | None,
    limit: int,
) -> ListPlacesRequest:
    bbox = None
    if None not in (min_lat, min_lng, max_lat, max_lng):
        bbox = (min_lat, min_lng, max_lat, max_lng)
    return ListPlacesRequest(
        owner_id=owner_id,
        category=category,
        bbox=bbox,
        limit=limit,
    )


def _body_fields_set(body) -> frozenset[str]:
    return frozenset(
        getattr(body, "model_fields_set", None)
        or getattr(body, "__fields_set__", set())
        or set()
    )


def to_patch_place_request(place_id: int, body: PlacePatchBody) -> PatchPlaceRequest:
    fields_set = _body_fields_set(body)
    lat = body.geo.latitude if body.geo is not None else None
    lng = body.geo.longitude if body.geo is not None else None
    return PatchPlaceRequest(
        place_id=place_id,
        name=body.name,
        about=body.about,
        category=body.category,
        lat=lat,
        lng=lng,
        attrs=body.attrs,
        schedule=body.schedule,
        pin_style_id=body.pin_style_id,
        chat_theme_id=body.chat_theme_id,
        city_id=body.city_id,
        contacts=body.contacts,
        fields_set=fields_set,
    )


def to_delete_place_request(place_id: int) -> DeletePlaceRequest:
    return DeletePlaceRequest(place_id=place_id)


def to_create_product_request(body: ProductCreateBody) -> CreateProductRequest:
    return CreateProductRequest(
        place_id=body.place_id,
        name=body.name,
        description=body.description or "",
        price=body.price,
        category=body.category,
        schedule=body.schedule,
    )


def to_list_products_request(
    *,
    place_id: int | None,
    category: str | None,
    limit: int,
) -> ListProductsRequest:
    return ListProductsRequest(place_id=place_id, category=category, limit=limit)


def to_patch_product_request(product_id: int, body: ProductPatchBody) -> PatchProductRequest:
    return PatchProductRequest(
        product_id=product_id,
        name=body.name,
        description=body.description,
        price=body.price,
        category=body.category,
        schedule=body.schedule,
        fields_set=_body_fields_set(body),
    )


def to_delete_product_request(product_id: int) -> DeleteProductRequest:
    return DeleteProductRequest(product_id=product_id)
