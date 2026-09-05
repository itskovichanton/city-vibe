"""E2E products: categories, CRUD, search."""

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
def test_products_crud_and_search(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]
    compose = live_backend["compose_file"]
    ensure_attr_schema(compose, "bars")

    with httpx.Client(base_url=gateway, timeout=45.0) as client:
        cats = get_json(client, "/product-categories")
        assert isinstance(cats, list) and cats
        codes = {c["code"] for c in cats if isinstance(c, dict)}
        assert "food" in codes
        assert "yoga_class" in codes

        user = register_and_verify(client, mailhog=mailhog)
        city_id = user["city_id"]
        owner_id = user["user_id"]
        suffix = uuid.uuid4().hex[:8]
        place_name = f"E2E Product Place {suffix}"

        pin = get_json(client, "/pin-styles/default")
        theme = get_json(client, "/chat-themes/default")
        pin_id = int(pin["id"]) if isinstance(pin, dict) else None
        theme_id = int(theme["id"]) if isinstance(theme, dict) else None

        place = post_json(
            client,
            "/places",
            {
                "name": place_name,
                "about": "Место для e2e продуктов",
                "category": "bars",
                "owner_id": owner_id,
                "city_id": city_id,
                "geo": {"latitude": 55.751244, "longitude": 37.618423},
                "attrs": {"has_wifi": True, "price_level": 2},
                "pin_style_id": pin_id,
                "chat_theme_id": theme_id,
            },
        )
        place_id = int(place["id"])
        product_name = f"E2E Сет {suffix}"

        created = post_json(
            client,
            "/products",
            {
                "place_id": place_id,
                "name": product_name,
                "description": "Тестовый сет роллов",
                "price": 890,
                "category": "food",
            },
        )
        product_id = int(created["id"])
        assert created["name"] == product_name
        assert created.get("category") == "food"
        assert created.get("place", {}).get("id") == place_id

        fetched = get_json(client, f"/products/{product_id}")
        assert int(fetched["id"]) == product_id
        assert fetched.get("place", {}).get("city_id") == city_id

        listed = get_json(client, f"/products?place_id={place_id}")
        assert isinstance(listed, list)
        assert any(int(p["id"]) == product_id for p in listed if isinstance(p, dict))

        patched = patch_json(client, f"/products/{product_id}", {"price": 990, "description": "Обновлённый сет"})
        assert patched.get("price") == 990
        assert "Обновлённый" in patched.get("description", "")

        search = post_json(
            client,
            "/products/search",
            {
                "city_id": city_id,
                "category": "food",
                "q": suffix,
                "price_from": 500,
                "price_to": 1500,
                "limit": 20,
                "page": 1,
                "sort_by": "price",
            },
        )
        assert isinstance(search.get("items"), list)
        assert search.get("total", 0) >= 1
        assert any(int(p["id"]) == product_id for p in search["items"])

        deleted = delete_json(client, f"/products/{product_id}")
        assert deleted.get("ok") is True

        r = client.get(f"/products/{product_id}")
        data = r.json()
        assert r.status_code >= 400 or "error" in data

        delete_json(client, f"/places/{place_id}")


@pytest.mark.e2e
def test_products_search_by_place_name_and_events(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]
    compose = live_backend["compose_file"]
    ensure_attr_schema(compose, "cafes")
    ensure_attr_schema(compose, "concerts")

    with httpx.Client(base_url=gateway, timeout=45.0) as client:
        user = register_and_verify(client, mailhog=mailhog)
        city_id = user["city_id"]
        owner_id = user["user_id"]
        suffix = uuid.uuid4().hex[:8]

        pin = get_json(client, "/pin-styles/default")
        theme = get_json(client, "/chat-themes/default")
        pin_id = int(pin["id"]) if isinstance(pin, dict) else None
        theme_id = int(theme["id"]) if isinstance(theme, dict) else None

        cafe = post_json(
            client,
            "/places",
            {
                "name": f"Кафе Мечта {suffix}",
                "about": "Кофейня e2e",
                "category": "cafes",
                "owner_id": owner_id,
                "city_id": city_id,
                "geo": {"latitude": 55.03, "longitude": 82.92},
                "attrs": {},
                "pin_style_id": pin_id,
                "chat_theme_id": theme_id,
            },
        )
        cafe_id = int(cafe["id"])
        combo = post_json(
            client,
            "/products",
            {
                "place_id": cafe_id,
                "name": f"Комбо кофе {suffix}",
                "description": "Два кофе по цене одного",
                "price": 250,
                "category": "coffee",
            },
        )
        combo_id = int(combo["id"])

        by_q = post_json(
            client,
            "/products/search",
            {"city_id": city_id, "q": "Мечта", "category": "coffee", "limit": 20},
        )
        assert any(int(p["id"]) == combo_id for p in by_q.get("items") or [])

        by_place = post_json(
            client,
            "/products/search",
            {
                "city_id": city_id,
                "place_name": "Мечта",
                "place_category": "cafes",
                "category": "coffee",
                "limit": 20,
            },
        )
        assert any(int(p["id"]) == combo_id for p in by_place.get("items") or [])

        phil = post_json(
            client,
            "/places",
            {
                "name": f"Филармония {suffix}",
                "about": "Концертный зал e2e",
                "category": "concerts",
                "owner_id": owner_id,
                "city_id": city_id,
                "geo": {"latitude": 55.028, "longitude": 82.921},
                "attrs": {},
                "pin_style_id": pin_id,
                "chat_theme_id": theme_id,
            },
        )
        phil_id = int(phil["id"])
        parker = post_json(
            client,
            "/products",
            {
                "place_id": phil_id,
                "name": f"Чарли Паркер {suffix}",
                "description": "Джазовый вечер",
                "price": 1500,
                "category": "concert",
                "schedule": {
                    "timezone": "Asia/Novosibirsk",
                    "periods": [],
                    "exceptions": [],
                    "events": [
                        {
                            "start": "2026-10-05T19:00:00",
                            "end": "2026-10-05T22:00:00",
                            "note": "Чарли Паркер",
                        }
                    ],
                },
            },
        )
        parker_id = int(parker["id"])
        dated = post_json(
            client,
            "/products/search",
            {
                "city_id": city_id,
                "category": "concert",
                "date_from": "2026-10-01",
                "date_to": "2026-10-31",
                "q": suffix,
                "include_past": True,
                "limit": 20,
            },
        )
        assert any(int(p["id"]) == parker_id for p in dated.get("items") or [])

        freebie = post_json(
            client,
            "/products",
            {
                "place_id": cafe_id,
                "name": f"Гостевой кофе {suffix}",
                "description": "Бесплатно, см. описание",
                "price": None,
                "category": "coffee",
            },
        )
        assert freebie.get("price") is None

        delete_json(client, f"/products/{combo_id}")
        delete_json(client, f"/products/{parker_id}")
        delete_json(client, f"/products/{int(freebie['id'])}")
        delete_json(client, f"/places/{cafe_id}")
        delete_json(client, f"/places/{phil_id}")
