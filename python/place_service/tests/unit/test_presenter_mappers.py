"""Юнит-тесты presenter/mappers place-service."""

from __future__ import annotations

from python.place_service.src.place_service.presenter.mappers import (
    to_create_place_request,
    to_create_product_request,
    to_delete_place_request,
    to_list_places_request,
    to_nearest_city_request,
    to_patch_place_request,
    to_patch_product_request,
)
from python.place_service.src.place_service.presenter.models import (
    GeoIn,
    PlaceCreateBody,
    PlacePatchBody,
    ProductCreateBody,
    ProductPatchBody,
)


def test_to_nearest_city_request():
    req = to_nearest_city_request(55.75, 37.62)
    assert req.lat == 55.75
    assert req.lng == 37.62


def test_to_create_place_request():
    body = PlaceCreateBody(
        name="Cafe",
        about="Nice",
        category="cafes",
        owner_id=1,
        geo=GeoIn(latitude=55.0, longitude=37.0),
        attrs={"outdoor_seating": True},
    )
    req = to_create_place_request(body)
    assert req.name == "Cafe"
    assert req.lat == 55.0
    assert req.category == "cafes"


def test_to_list_places_request_bbox():
    req = to_list_places_request(
        owner_id=5,
        category="bars",
        min_lat=55.0,
        min_lng=37.0,
        max_lat=56.0,
        max_lng=38.0,
        limit=50,
    )
    assert req.bbox == (55.0, 37.0, 56.0, 38.0)
    assert req.owner_id == 5


def test_to_patch_place_request_fields_set():
    body = PlacePatchBody(about="Updated", pin_style_id=3)
    req = to_patch_place_request(10, body)
    assert req.place_id == 10
    assert req.about == "Updated"
    assert "pin_style_id" in req.fields_set


def test_to_delete_place_request():
    req = to_delete_place_request(42)
    assert req.place_id == 42


def test_to_create_product_request():
    body = ProductCreateBody(
        place_id=7,
        name="Сет роллов",
        description="Филадельфия",
        price=890,
        category="food",
    )
    req = to_create_product_request(body)
    assert req.place_id == 7
    assert req.category == "food"
    assert req.price == 890


def test_to_create_product_request_null_price():
    body = ProductCreateBody(
        place_id=7,
        name="Гостевой визит",
        category="fitness_class",
    )
    req = to_create_product_request(body)
    assert req.price is None


def test_to_patch_product_request_schedule_null():
    body = ProductPatchBody(schedule=None)
    req = to_patch_product_request(3, body)
    assert req.product_id == 3
    assert "schedule" in req.fields_set
    assert req.schedule is None
