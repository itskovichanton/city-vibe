"""Unit: ProductSearchRequest + schedule SQL (periods, exceptions, events)."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from python.place_service.src.place_service.entities.search import (
    PlaceSearchRequest,
    ProductSearchRequest,
    SearchOpenAt,
    SearchOpenInterval,
)
from python.place_service.src.place_service.infra.schedule_filter import (
    compile_date_range_filters,
    compile_include_past_filter,
    compile_open_at_filters,
)
from python.place_service.src.place_service.infra.search_sql import sql_not_in, unique_positive_ids


def test_product_search_ok():
    body = ProductSearchRequest(
        city_id=3,
        category="food",
        q="ролл",
        price_from=100,
        price_to=1000,
        sort_by="price",
    )
    assert body.category == "food"
    assert body.q == "ролл"


def test_product_search_q_without_category():
    body = ProductSearchRequest(city_id=3, q="Мечта")
    assert body.category is None
    assert body.q == "Мечта"


def test_product_search_place_name_anchor():
    body = ProductSearchRequest(city_id=3, place_name="Мечта", place_category="cafes")
    assert body.place_name == "Мечта"
    assert body.place_category == "cafes"


def test_product_search_needs_anchor():
    with pytest.raises(ValidationError):
        ProductSearchRequest(city_id=3)


def test_place_search_name_without_category():
    body = PlaceSearchRequest(city_id=3, name="Мечта")
    assert body.category is None
    assert body.name == "Мечта"


def test_place_search_needs_anchor():
    with pytest.raises(ValidationError):
        PlaceSearchRequest(city_id=3)


def test_product_search_unknown_category():
    with pytest.raises(ValidationError):
        ProductSearchRequest(city_id=3, category="restaurants")


def test_product_search_price_range_invalid():
    with pytest.raises(ValidationError):
        ProductSearchRequest(city_id=3, category="food", price_from=500, price_to=100)


def test_product_search_distance_requires_geo():
    with pytest.raises(ValidationError):
        ProductSearchRequest(city_id=3, category="food", sort_by="distance")


def test_product_search_empty_open_at():
    with pytest.raises(ValidationError):
        ProductSearchRequest(city_id=3, category="concert", open_at=[])


def test_product_search_exclude_fields():
    body = ProductSearchRequest(
        city_id=3,
        q="кофе",
        exclude_ids=[1, 2],
        exclude_place_ids=[10],
        one_per_place=True,
        date_from=date(2026, 10, 1),
        timezone="Asia/Novosibirsk",
        sort_by="event_start",
    )
    assert body.exclude_ids == [1, 2]
    assert body.exclude_place_ids == [10]
    assert body.one_per_place is True
    assert body.include_past is False


def test_sql_not_in_caps_and_uniques():
    params: dict = {}
    clause = sql_not_in("p.id", [1, 1, 0, -3, 2], params, prefix="exid")
    assert clause is not None
    assert "p.id NOT IN" in clause
    assert params["exid_0"] == 1
    assert params["exid_1"] == 2
    assert unique_positive_ids([1, 1, 2]) == [1, 2]


def test_open_at_sql_includes_exceptions():
    sql, params = compile_open_at_filters(
        [SearchOpenAt(weekday=5, intervals=[SearchOpenInterval(open="20:00")])],
        include_exceptions=True,
        schedule_column="p.schedule",
    )
    assert "p.schedule" in sql
    assert "exceptions" in sql
    assert "periods" in sql
    assert params["oa_0_wd"] == 5
    assert params["oa_0_0_t"] == "20:00"


def test_open_at_sql_includes_events():
    sql, _params = compile_open_at_filters(
        [SearchOpenAt(weekday=0, intervals=[SearchOpenInterval(open="19:00")])],
        include_exceptions=True,
        include_events=True,
        schedule_column="p.schedule",
    )
    assert "events" in sql
    assert "p.schedule" in sql


def test_open_at_sql_places_skip_exceptions():
    sql, _params = compile_open_at_filters(
        [SearchOpenAt(weekday=0, intervals=[SearchOpenInterval(open="18:00")])],
        include_exceptions=False,
        schedule_column="schedule",
    )
    assert "exceptions" not in sql
    assert "schedule" in sql


def test_date_range_sql_uses_events_and_exceptions():
    sql, params = compile_date_range_filters(
        date_from=date(2026, 10, 1),
        date_to=date(2026, 10, 31),
        schedule_column="p.schedule",
    )
    assert "events" in sql
    assert "exceptions" in sql
    assert params["df"] == date(2026, 10, 1)
    assert params["dt"] == date(2026, 10, 31)


def test_include_past_filter_drops_ended_events():
    sql, params = compile_include_past_filter(
        include_past=False,
        timezone="Asia/Novosibirsk",
        schedule_column="p.schedule",
    )
    assert "events" in sql
    assert "AT TIME ZONE" in sql
    assert "past_now" in params


def test_include_past_true_is_noop():
    sql, params = compile_include_past_filter(
        include_past=True,
        timezone="Asia/Novosibirsk",
        schedule_column="p.schedule",
    )
    assert sql == "TRUE"
    assert params == {}
