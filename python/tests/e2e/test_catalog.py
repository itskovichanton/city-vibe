"""E2E catalog: cities, nearest, categories, attr-schemas."""

from __future__ import annotations

import httpx
import pytest

from python.tests.e2e.helpers import assert_http_error, ensure_attr_schema, get_json

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_cities_categories_attr_schemas(live_backend):
    gateway = live_backend["gateway"]
    compose = live_backend["compose_file"]
    ensure_attr_schema(compose, "bars")

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        cities = get_json(client, "/cities")
        assert isinstance(cities, list) and len(cities) >= 1
        city = cities[0]
        assert "id" in city and "name" in city
        city_id = int(city["id"])

        one = get_json(client, f"/cities/{city_id}")
        assert isinstance(one, dict)
        assert int(one["id"]) == city_id

        # Москва-ish coords → ближайший major city
        nearest = get_json(client, "/cities/nearest?lat=55.75&lng=37.62")
        assert isinstance(nearest, dict)
        assert nearest.get("id")
        assert "distance_m" in nearest

        categories = get_json(client, "/categories")
        assert isinstance(categories, list) and categories
        codes = {c["code"] for c in categories if isinstance(c, dict)}
        assert "bars" in codes or "cafes" in codes or "restaurants" in codes

        schemas = get_json(client, "/attr-schemas")
        assert isinstance(schemas, list)
        bars_schema = get_json(client, "/attr-schemas/bars")
        assert isinstance(bars_schema, dict)
        assert bars_schema.get("category_code") == "bars"
        assert isinstance(bars_schema.get("json_schema"), dict)

        compact = get_json(client, "/attr-schemas/bars?compact=true")
        assert isinstance(compact, dict)
        assert compact.get("compact") is True

        assert_http_error(client, "get", "/cities/999999999")
        assert_http_error(client, "get", "/attr-schemas/no_such_category_zzz")
