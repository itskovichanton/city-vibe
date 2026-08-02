"""Юнит-тесты presenter/mappers.py."""

from __future__ import annotations

from types import SimpleNamespace

from python.libs.entities.place import PlaceCategory
from python.user_service.src.user_service.presenter.mappers import (
    parse_category_codes,
    to_complete_onboarding_request,
    to_create_user_request,
    to_delete_user_request,
    to_update_bio_request,
    to_update_profile_request,
    to_upload_avatar_request,
)


def test_parse_category_codes_skips_unknown():
    assert parse_category_codes(["bars", "unknown", "cafes"]) == [
        PlaceCategory.BARS,
        PlaceCategory.CAFES,
    ]
    assert parse_category_codes(None) is None


def test_to_create_user_request():
    body = SimpleNamespace(
        name="Anna",
        gender="female",
        age=25,
        short_bio="hi",
        favorite_categories=["bars"],
        city_id=1,
        birthdate=None,
        auth_account_id=10,
    )
    req = to_create_user_request(body)
    assert req.name == "Anna"
    assert req.favorite_categories == [PlaceCategory.BARS]
    assert req.auth_account_id == 10


def test_to_update_profile_request():
    body = SimpleNamespace(name="Maria", favorite_categories=["parks"])
    req = to_update_profile_request(7, body)
    assert req.user_id == 7
    assert req.name == "Maria"
    assert req.favorite_categories == [PlaceCategory.PARKS]


def test_to_update_bio_request():
    body = SimpleNamespace(long_bio="About me")
    req = to_update_bio_request(3, body)
    assert req.user_id == 3
    assert req.long_bio == "About me"


def test_to_complete_onboarding_request():
    req = to_complete_onboarding_request(11)
    assert req.user_id == 11


def test_to_delete_user_request():
    req = to_delete_user_request(99)
    assert req.user_id == 99


def test_to_upload_avatar_request():
    req = to_upload_avatar_request(
        5,
        data=b"png",
        content_type="image/png",
        extension=".png",
    )
    assert req.user_id == 5
    assert req.data == b"png"
    assert req.content_type == "image/png"
    assert req.extension == ".png"
