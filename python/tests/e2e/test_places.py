"""E2E places: CRUD + search."""

from __future__ import annotations

import uuid

import httpx
import pytest

from python.tests.e2e.helpers import (
    delete_json,
    ensure_attr_schema,
    get_json,
    patch_json,
    post_json,
    register_and_verify,
)

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_places_crud_and_search(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]
    compose = live_backend["compose_file"]
    ensure_attr_schema(compose, "bars")

    with httpx.Client(base_url=gateway, timeout=45.0) as client:
        user = register_and_verify(client, mailhog=mailhog)
        city_id = user["city_id"]
        owner_id = user["user_id"]
        suffix = uuid.uuid4().hex[:8]
        place_name = f"E2E Bar {suffix}"

        pin = get_json(client, "/pin-styles/default")
        theme = get_json(client, "/chat-themes/default")
        pin_id = int(pin["id"]) if isinstance(pin, dict) else None
        theme_id = int(theme["id"]) if isinstance(theme, dict) else None

        created = post_json(
            client,
            "/places",
            {
                "name": place_name,
                "about": "Интеграционный бар для e2e",
                "category": "bars",
                "owner_id": owner_id,
                "city_id": city_id,
                "geo": {"latitude": 55.751244, "longitude": 37.618423},
                "attrs": {"has_wifi": True, "price_level": 2},
                "schedule": {
                    "timezone": "Europe/Moscow",
                    "periods": [
                        {
                            "weekday": 0,
                            "closed": False,
                            "intervals": [{"open": "18:00", "close": "02:00"}],
                        }
                    ],
                    "exceptions": [],
                },
                "pin_style_id": pin_id,
                "chat_theme_id": theme_id,
                "contacts": [{"type": "phone", "value": "+79991234567"}],
            },
        )
        place_id = int(created["id"])
        assert created["name"] == place_name
        assert created.get("category") == "bars"
        assert created.get("attrs", {}).get("has_wifi") is True

        fetched = get_json(client, f"/places/{place_id}")
        assert isinstance(fetched, dict)
        assert int(fetched["id"]) == place_id

        listed = get_json(client, f"/places?owner_id={owner_id}")
        assert isinstance(listed, list)
        assert any(int(p["id"]) == place_id for p in listed if isinstance(p, dict))

        patched = patch_json(
            client,
            f"/places/{place_id}",
            {"about": "Обновлённое описание e2e", "attrs": {"has_wifi": False, "price_level": 3}},
        )
        assert "Обновлённое" in patched.get("about", "")
        assert patched.get("attrs", {}).get("price_level") == 3

        search = post_json(
            client,
            "/places/search",
            {
                "city_id": city_id,
                "category": "bars",
                "name": suffix,
                "limit": 20,
                "page": 1,
                "sort_by": "distance",
                "my_geo": {"lat": 55.75, "lng": 37.62},
            },
        )
        assert isinstance(search.get("items"), list)
        assert search.get("total", 0) >= 1
        assert any(int(p["id"]) == place_id for p in search["items"])

        # bbox list
        bbox = get_json(
            client,
            "/places?min_lat=55.7&min_lng=37.5&max_lat=55.8&max_lng=37.7&limit=50",
        )
        assert isinstance(bbox, list)

        deleted = delete_json(client, f"/places/{place_id}")
        assert deleted.get("ok") is True

        r = client.get(f"/places/{place_id}")
        data = r.json()
        assert r.status_code >= 400 or "error" in data
