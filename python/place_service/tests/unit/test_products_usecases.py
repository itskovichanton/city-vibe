"""Юнит-тесты use-cases products (create, search)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from python.libs.entities.geo import GeoLocation
from python.libs.entities.place import Place, PlaceCategory, Product, ProductCategory
from python.libs.entities.schedule import WeeklySchedule
from python.place_service.src.place_service.entities.common import CreateProductRequest
from python.place_service.src.place_service.entities.search import ProductSearchRequest
from python.place_service.src.place_service.usecase.products import CreateProductUseCaseImpl
from python.place_service.src.place_service.usecase.search_products import SearchProductsUseCaseImpl


def _sample_place(**kwargs) -> Place:
    defaults = dict(
        id=10,
        deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        geo=GeoLocation.of(55.75, 37.62),
        name="Studio",
        about="About",
        category=PlaceCategory.GYMS,
        owner_id=10,
        rating=None,
        album=None,
        contacts=[],
        attrs={},
        schedule=WeeklySchedule(timezone="Europe/Moscow", periods=[], exceptions=[]),
        pin_style_id=1,
        chat_theme_id=2,
        city_id=3,
    )
    defaults.update(kwargs)
    return Place(**defaults)


def _sample_product(**kwargs) -> Product:
    defaults = dict(
        id=1,
        deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        place_id=10,
        name="Хатха-йога",
        description="60 минут",
        price=Decimal("700.00"),
        category=ProductCategory.YOGA_CLASS,
        schedule=None,
    )
    defaults.update(kwargs)
    return Product(**defaults)


@pytest.mark.asyncio
async def test_create_product_use_case():
    place = _sample_place()
    product = _sample_product()

    product_repo = AsyncMock()
    product_repo.create = AsyncMock(return_value=product)
    product_category_repo = AsyncMock()
    product_category_repo.get_by_code = AsyncMock(return_value=object())
    place_repo = AsyncMock()
    place_repo.get_by_id = AsyncMock(return_value=place)

    uc = object.__new__(CreateProductUseCaseImpl)
    uc.product_repo = product_repo
    uc.product_category_repo = product_category_repo
    uc.place_repo = place_repo

    result = await uc.execute(
        CreateProductRequest(
            place_id=10,
            name="Хатха-йога",
            description="60 минут",
            price=700,
            category="yoga_class",
        )
    )

    assert result["name"] == "Хатха-йога"
    assert result["category"] == "yoga_class"
    assert result["price"] == 700.0
    assert result["place"]["id"] == 10
    product_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_product_nullable_price():
    place = _sample_place()
    product = _sample_product(price=None, name="Гостевая растяжка")

    product_repo = AsyncMock()
    product_repo.create = AsyncMock(return_value=product)
    product_category_repo = AsyncMock()
    product_category_repo.get_by_code = AsyncMock(return_value=object())
    place_repo = AsyncMock()
    place_repo.get_by_id = AsyncMock(return_value=place)

    uc = object.__new__(CreateProductUseCaseImpl)
    uc.product_repo = product_repo
    uc.product_category_repo = product_category_repo
    uc.place_repo = place_repo

    result = await uc.execute(
        CreateProductRequest(
            place_id=10,
            name="Гостевая растяжка",
            description="45 минут",
            price=None,
            category="yoga_class",
        )
    )
    assert result["price"] is None
    kwargs = product_repo.create.await_args.kwargs
    assert kwargs["price"] is None


@pytest.mark.asyncio
async def test_search_products_use_case():
    product = _sample_product(id=42)
    place = _sample_place(id=10)
    search_result = MagicMock()
    search_result.items = [product]
    search_result.distances_m = {42: 123.456}
    search_result.total = 1
    search_result.page = 1
    search_result.limit = 20

    product_category_repo = AsyncMock()
    product_category_repo.get_by_code = AsyncMock(return_value=object())
    city_repo = AsyncMock()
    city_repo.get_by_id = AsyncMock(return_value=object())
    place_repo = AsyncMock()
    place_repo.get_by_id = AsyncMock(return_value=place)
    product_search_repo = AsyncMock()
    product_search_repo.search = AsyncMock(return_value=search_result)

    uc = object.__new__(SearchProductsUseCaseImpl)
    uc.product_category_repo = product_category_repo
    uc.city_repo = city_repo
    uc.place_repo = place_repo
    uc.product_search_repo = product_search_repo

    body = ProductSearchRequest(city_id=3, category="yoga_class")
    result = await uc.execute(body)

    assert result["total"] == 1
    assert result["items"][0]["id"] == 42
    assert result["items"][0]["distance_m"] == 123.5
    assert result["items"][0]["place"]["name"] == "Studio"


@pytest.mark.asyncio
async def test_search_products_without_category():
    product_category_repo = AsyncMock()
    city_repo = AsyncMock()
    city_repo.get_by_id = AsyncMock(return_value=object())
    search_result = MagicMock()
    search_result.items = []
    search_result.distances_m = {}
    search_result.total = 0
    search_result.page = 1
    search_result.limit = 20
    product_search_repo = AsyncMock()
    product_search_repo.search = AsyncMock(return_value=search_result)

    uc = object.__new__(SearchProductsUseCaseImpl)
    uc.product_category_repo = product_category_repo
    uc.city_repo = city_repo
    uc.place_repo = AsyncMock()
    uc.product_search_repo = product_search_repo

    await uc.execute(ProductSearchRequest(city_id=3, q="Мечта"))
    product_category_repo.get_by_code.assert_not_called()
    product_search_repo.search.assert_awaited_once()
