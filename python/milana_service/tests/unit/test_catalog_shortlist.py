"""Милана: shortlist справочников, не полный мир."""

from python.milana_service.src.milana_service.agent.places_nl_search import PlacesNlSearchAgent


def test_slim_catalog_items_keeps_why():
    slim = PlacesNlSearchAgent._slim_catalog_items(
        [
            {"code": "coffee", "title": "Кофе", "title_en": "Coffee", "why": "алиас «сладенькое»", "score": 3.9},
            {"code": None},
        ],
        city_keys=("code", "title", "why"),
    )
    assert slim == [{"code": "coffee", "title": "Кофе", "why": "алиас «сладенькое»"}]
