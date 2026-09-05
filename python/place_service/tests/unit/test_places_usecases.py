"""Юнит-тесты use-cases places (create, patch, delete, search)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from python.libs.entities.geo import GeoLocation
from python.libs.entities.place import Place, PlaceCategory
from python.libs.entities.schedule import WeeklySchedule
from python.place_service.src.place_service.entities.common import (
    CreatePlaceRequest,
    DeletePlaceRequest,
    PatchPlaceRequest,
)
from python.place_service.src.place_service.entities.search import PlaceSearchRequest
from python.place_service.src.place_service.usecase.places import (
    CreatePlaceUseCaseImpl,
    DeletePlaceUseCaseImpl,
    PatchPlaceUseCaseImpl,
)
from python.place_service.src.place_service.usecase.search_places import SearchPlacesUseCaseImpl


def _sample_place(**kwargs) -> Place:
    defaults = dict(
        id=1,
        deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        geo=GeoLocation.of(55.75, 37.62),
        name="Bar",
        about="About",
        category=PlaceCategory.BARS,
        owner_id=10,
        rating=None,
        album=None,
        contacts=[],
        attrs={"has_wifi": True},
        schedule=WeeklySchedule(timezone="Europe/Moscow", periods=[], exceptions=[]),
        pin_style_id=1,
        chat_theme_id=2,
        city_id=3,
    )
    defaults.update(kwargs)
    return Place(**defaults)


@pytest.mark.asyncio
async def test_create_place_use_case():
    place = _sample_place()
    place_repo = AsyncMock()
    place_repo.create = AsyncMock(return_value=place)

    attrs_validator = AsyncMock()
    attrs_validator.resolve_and_validate = AsyncMock(return_value={"has_wifi": True})

    uc = object.__new__(CreatePlaceUseCaseImpl)
    uc.place_repo = place_repo
    uc.place_attrs_validator = attrs_validator

    result = await uc.execute(
        CreatePlaceRequest(
            name="Bar",
            about="About",
            category="bars",
            owner_id=10,
            lat=55.75,
            lng=37.62,
            attrs={"has_wifi": True},
        )
    )

    assert result["name"] == "Bar"
    assert result["category"] == "bars"
    place_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_place_use_case():
    existing = _sample_place(id=5)
    updated = _sample_place(id=5, about="New about", attrs={"has_wifi": False})

    place_repo = AsyncMock()
    place_repo.get_by_id = AsyncMock(return_value=existing)
    place_repo.update = AsyncMock(return_value=updated)

    attrs_validator = AsyncMock()
    attrs_validator.resolve_and_validate = AsyncMock(return_value={"has_wifi": False})

    uc = object.__new__(PatchPlaceUseCaseImpl)
    uc.place_repo = place_repo
    uc.place_attrs_validator = attrs_validator

    result = await uc.execute(
        PatchPlaceRequest(
            place_id=5,
            about="New about",
            attrs={"has_wifi": False},
        )
    )

    assert "New about" in result["about"]
    place_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_place_use_case():
    place_repo = AsyncMock()
    place_repo.soft_delete = AsyncMock(return_value=True)

    uc = object.__new__(DeletePlaceUseCaseImpl)
    uc.place_repo = place_repo

    result = await uc.execute(DeletePlaceRequest(place_id=7))
    assert result.ok is True
    assert result.place_id == 7


@pytest.mark.asyncio
async def test_search_places_use_case():
    place = _sample_place(id=99)
    search_result = MagicMock()
    search_result.items = [place]
    search_result.distances_m = {99: 123.456}
    search_result.total = 1
    search_result.page = 1
    search_result.limit = 20

    category_repo = AsyncMock()
    category_repo.get_by_code = AsyncMock(return_value=object())
    city_repo = AsyncMock()
    city_repo.get_by_id = AsyncMock(return_value=object())
    attr_schema_repo = AsyncMock()
    place_search_repo = AsyncMock()
    place_search_repo.search = AsyncMock(return_value=search_result)

    uc = object.__new__(SearchPlacesUseCaseImpl)
    uc.category_repo = category_repo
    uc.city_repo = city_repo
    uc.attr_schema_repo = attr_schema_repo
    uc.place_search_repo = place_search_repo

    body = PlaceSearchRequest(city_id=1, category="bars")
    result = await uc.execute(body)

    assert result["total"] == 1
    assert result["items"][0]["id"] == 99
    assert result["items"][0]["distance_m"] == 123.5


@pytest.mark.asyncio
async def test_search_places_without_category():
    category_repo = AsyncMock()
    city_repo = AsyncMock()
    city_repo.get_by_id = AsyncMock(return_value=object())
    search_result = MagicMock()
    search_result.items = []
    search_result.distances_m = {}
    search_result.total = 0
    search_result.page = 1
    search_result.limit = 20
    place_search_repo = AsyncMock()
    place_search_repo.search = AsyncMock(return_value=search_result)

    uc = object.__new__(SearchPlacesUseCaseImpl)
    uc.category_repo = category_repo
    uc.city_repo = city_repo
    uc.attr_schema_repo = AsyncMock()
    uc.place_search_repo = place_search_repo

    await uc.execute(PlaceSearchRequest(city_id=1, name="Мечта"))
    category_repo.get_by_code.assert_not_called()
