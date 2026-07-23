"""Unit-тесты variant B helpers."""

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
        known_codes={"theaters", "restaurants"},
    )
    assert len(out) == 1
    assert out[0]["category"] == "theaters"
    assert out[0]["why"] == "спектакль"
    assert "plan_skip_unknown_category" in logs


def test_parse_build_merges_why():
    agent = PlacesNlSearchAgent.__new__(PlacesNlSearchAgent)
    plan = [{"intent": "Ужин", "category": "restaurants", "why": "паркинг"}]
    out = agent._parse_build(
        {"steps": [{"search": {"city_id": 3, "category": "restaurants"}}]},
        plan_steps=plan,
    )
    assert out[0]["intent"] == "Ужин"
    assert out[0]["why"] == "паркинг"
    assert out[0]["search"]["category"] == "restaurants"
