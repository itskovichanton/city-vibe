"""Unit-тесты variant B helpers."""

from unittest.mock import AsyncMock

import pytest

from python.libs.utils.schema_compact import compact_json_schema
from python.milana_service.src.milana_service.agent.places_nl_search import PlacesNlSearchAgent


def test_compact_strips_description():
    raw = {
        "type": "object",
        "properties": {
            "has_parking": {"type": "boolean", "description": "Есть парковка"},
            "dress_code": {
                "type": "string",
                "enum": ["casual", "formal"],
                "description": "Дресс-код",
            },
            "cuisine": {
                "type": "array",
                "description": "кухни",
                "items": {"type": "string", "enum": ["italian", "asian"]},
            },
        },
    }
    c = compact_json_schema(raw)
    assert "description" not in c["properties"]["has_parking"]
    assert c["properties"]["dress_code"]["enum"] == ["casual", "formal"]
    assert c["properties"]["cuisine"]["items"]["enum"] == ["italian", "asian"]


def test_parse_plan_filters_unknown():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    logs = []
    agent._log = lambda event, **kw: logs.append(event)
    out = agent._parse_plan(
        {
            "steps": [
                {"intent": "театр", "category": "theaters", "why": "спектакль"},
                {"intent": "xxx", "category": "no_such", "why": "bad"},
            ]
        },
        known_place_codes={"theaters", "restaurants"},
        known_product_codes={"yoga_class", "food"},
    )
    assert len(out) == 1
    assert out[0]["category"] == "theaters"
    assert out[0]["domain"] == "place"
    assert out[0]["why"] == "спектакль"
    assert "plan_skip_unknown_category" in logs


def test_parse_plan_product_domain():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    logs = []
    agent._log = lambda event, **kw: logs.append(event)
    out = agent._parse_plan(
        {
            "steps": [
                {"domain": "product", "intent": "йога", "category": "yoga_class", "why": "вечер"},
                {"domain": "product", "intent": "бар", "category": "bars", "why": "не тот справочник"},
                {"intent": "еда", "category": "food", "why": "без domain — infer"},
            ]
        },
        known_place_codes={"bars", "restaurants"},
        known_product_codes={"yoga_class", "food"},
    )
    assert [s["category"] for s in out] == ["yoga_class", "food"]
    assert out[0]["domain"] == "product"
    assert out[1]["domain"] == "product"


def test_parse_plan_place_name_without_category():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    logs = []
    agent._log = lambda event, **kw: logs.append(event)
    out = agent._parse_plan(
        {
            "steps": [
                {
                    "domain": "product",
                    "intent": "акции в Мечте",
                    "category": "",
                    "place_name": "Мечта",
                    "place_category": "cafes",
                    "why": "названное кафе",
                }
            ]
        },
        known_place_codes={"cafes", "bars"},
        known_product_codes={"coffee", "food"},
    )
    assert len(out) == 1
    assert out[0]["place_name"] == "Мечта"
    assert out[0]["place_category"] == "cafes"
    assert out[0]["category"] == ""


def test_parse_build_copies_place_name():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    plan = [
        {
            "domain": "product",
            "intent": "кофе",
            "category": "coffee",
            "why": "Мечта",
            "place_name": "Мечта",
            "place_category": "cafes",
        }
    ]
    out = agent._parse_build(
        {"steps": [{"domain": "product", "search": {"city_id": 3, "category": "coffee"}}]},
        plan_steps=plan,
    )
    assert out[0]["search"]["place_name"] == "Мечта"
    assert out[0]["search"]["place_category"] == "cafes"


def test_parse_build_merges_why():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    plan = [{"domain": "place", "intent": "Ужин", "category": "restaurants", "why": "паркинг"}]
    out = agent._parse_build(
        {"steps": [{"search": {"city_id": 3, "category": "restaurants"}}]},
        plan_steps=plan,
    )
    assert out[0]["intent"] == "Ужин"
    assert out[0]["why"] == "паркинг"
    assert out[0]["domain"] == "place"
    assert out[0]["search"]["category"] == "restaurants"


def test_normalize_product_search():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    out = agent._normalize_search(
        {"category": "food", "name": "роллы", "attrs": {"x": 1}, "sort_by": "rating"},
        city_id=3,
        my_geo=None,
        limit=5,
        domain="product",
    )
    assert out["q"] == "роллы"
    assert "attrs" not in out
    assert "name" not in out
    assert out.get("sort_by") is None
    assert out["city_id"] == 3
    assert out["limit"] == 5
    assert out["one_per_place"] is True


def test_normalize_default_distance():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    out = agent._normalize_search(
        {"category": "cafes"},
        city_id=3,
        my_geo={"lat": 55.0, "lng": 83.0},
        limit=5,
        domain="place",
        timezone="Asia/Novosibirsk",
    )
    assert out["sort_by"] == "distance"
    assert out["my_geo"]["lat"] == 55.0
    assert out["timezone"] == "Asia/Novosibirsk"


def test_apply_excludes_between_steps():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    body = {"city_id": 3, "category": "coffee"}
    agent._apply_excludes(
        body,
        domain="product",
        place_ids=[10, 11],
        product_ids=[1, 2],
    )
    assert body["exclude_ids"] == [1, 2]
    assert body["exclude_place_ids"] == [10, 11]


@pytest.mark.asyncio
async def test_resolve_place_name_injects_id():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    logs = []
    agent._log = lambda event, **kw: logs.append(event)
    agent.places = AsyncMock()
    agent.places.search = AsyncMock(return_value={"items": [{"id": 77, "name": "Кафе Мечта"}]})
    body = {"city_id": 3, "place_name": "Мечта", "place_category": "cafes", "category": "coffee"}
    ok = await agent._resolve_place_name(body, city_id=3)
    assert ok is True
    assert body["place_id"] == 77
    assert "place_name" not in body
    agent.places.search.assert_awaited_once()
    lookup = agent.places.search.await_args.args[0]
    assert lookup["name"] == "Мечта"
    assert lookup["category"] == "cafes"
    assert lookup["limit"] == 1


@pytest.mark.asyncio
async def test_resolve_place_name_miss():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    agent._log = lambda event, **kw: None
    agent.places = AsyncMock()
    agent.places.search = AsyncMock(return_value={"items": []})
    body = {"city_id": 3, "place_name": "Неттакого"}
    ok = await agent._resolve_place_name(body, city_id=3)
    assert ok is False
