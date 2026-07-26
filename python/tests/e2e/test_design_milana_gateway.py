"""E2E design + milana world + gateway health."""

from __future__ import annotations

import os

import httpx
import pytest

from python.tests.e2e.helpers import assert_http_error, ensure_attr_schema, get_json, post_json

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_design_pin_styles_and_chat_themes(live_backend):
    gateway = live_backend["gateway"]
    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        pins = get_json(client, "/pin-styles")
        assert isinstance(pins, list) and pins
        default_pin = get_json(client, "/pin-styles/default")
        assert isinstance(default_pin, dict)
        assert default_pin.get("code") == "default" or default_pin.get("id")
        pin_id = int(default_pin["id"])
        by_id = get_json(client, f"/pin-styles/{pin_id}")
        assert isinstance(by_id, dict)
        assert int(by_id["id"]) == pin_id

        themes = get_json(client, "/chat-themes")
        assert isinstance(themes, list) and themes
        default_theme = get_json(client, "/chat-themes/default")
        assert isinstance(default_theme, dict)
        theme_id = int(default_theme["id"])
        theme_by_id = get_json(client, f"/chat-themes/{theme_id}")
        assert int(theme_by_id["id"]) == theme_id

        assert_http_error(client, "get", "/pin-styles/999999999")
        assert_http_error(client, "get", "/chat-themes/999999999")


@pytest.mark.e2e
def test_milana_world_catalog(live_backend):
    gateway = live_backend["gateway"]
    compose = live_backend["compose_file"]
    ensure_attr_schema(compose, "bars")

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        world = get_json(client, "/milana/world")
        assert isinstance(world, dict)
        assert world.get("cities") or world.get("categories")

        cities = get_json(client, "/milana/cities")
        assert isinstance(cities, list) and cities

        categories = get_json(client, "/milana/categories")
        assert isinstance(categories, list) and categories

        schema = get_json(client, "/milana/attr-schemas/bars")
        assert isinstance(schema, dict)


@pytest.mark.e2e
def test_milana_nl_search_optional(live_backend):
    """NL-поиск требует DEEPSEEK_API_KEY — иначе skip."""
    if not os.environ.get("DEEPSEEK_API_KEY"):
        pytest.skip("DEEPSEEK_API_KEY не задан — milana NL search пропущен")

    gateway = live_backend["gateway"]
    with httpx.Client(base_url=gateway, timeout=120.0) as client:
        cities = get_json(client, "/cities")
        assert isinstance(cities, list) and cities
        city_id = int(cities[0]["id"])
        result = post_json(
            client,
            "/milana/places/search",
            {
                "q": "хочу бар с вайфаем вечером",
                "city_id": city_id,
                "my_geo": {"lat": 55.75, "lng": 37.62},
                "weekday": 4,
                "limit_per_step": 3,
            },
        )
        assert result.get("message")
        assert isinstance(result.get("plan"), list) or isinstance(result.get("steps"), list)


@pytest.mark.e2e
def test_gateway_health(live_backend):
    gateway = live_backend["gateway"]
    with httpx.Client(base_url=gateway, timeout=15.0) as client:
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        # gateway health может быть без result-обёртки
        payload = data.get("result") if isinstance(data, dict) and "result" in data else data
        assert isinstance(payload, dict)
        assert payload.get("gateway") == "ok" or payload.get("status") == "ok"
        backends = payload.get("backends") or {}
        for key in ("auth", "users", "places"):
            if key in backends:
                assert backends[key] == "ok"
