"""Гибридный catalog/match: порции effort + merge алиасов и LLM."""

from python.milana_service.src.milana_service.agent.catalog_hybrid import (
    chunk_rows,
    merge_hits,
    parse_llm_items,
)


def test_chunk_rows_by_effort():
    rows = [{"code": i} for i in range(12)]
    batches = chunk_rows(rows, 5)
    assert [len(b) for b in batches] == [5, 5, 2]
    assert chunk_rows(rows, 0) == []
    assert chunk_rows([], 10) == []
    huge = [{"code": i} for i in range(200)]
    capped = chunk_rows(huge, 200)
    assert all(len(b) <= 80 for b in capped)
    assert sum(len(b) for b in capped) == 200


def test_parse_llm_items_drops_unknown_and_weak():
    allowed = {"photo_session", "bakery_goods"}
    parsed = parse_llm_items(
        {
            "items": [
                {"key": "photo_session", "why": "фоткаться", "confidence": 0.9},
                {"key": "invented", "why": "нет", "confidence": 0.99},
                {"code": "bakery_goods", "why": "сладкое", "confidence": 0.2},
            ]
        },
        allowed,
    )
    assert [p["key"] for p in parsed] == ["photo_session"]


def test_merge_keeps_alias_and_llm():
    rows = {
        "photo_session": {"code": "photo_session", "title": "Фотосессия"},
        "bakery_goods": {"code": "bakery_goods", "title": "Выпечка"},
        "plumbing": {"code": "plumbing", "title": "Сантехника"},
    }
    cheap = [
        {"code": "bakery_goods", "title": "Выпечка", "why": "запрос про сладкое", "score": 7.8},
    ]
    llm = [
        {"key": "photo_session", "why": "фоткаться = фотосессия", "confidence": 0.92},
        {"key": "bakery_goods", "why": "сладкое", "confidence": 0.8},
    ]
    items = merge_hits(rows, cheap, llm, limit=8)
    codes = [row["code"] for row in items]
    assert "photo_session" in codes
    assert "bakery_goods" in codes
    assert "plumbing" not in codes
    photo = next(row for row in items if row["code"] == "photo_session")
    assert photo["source"] == "llm"
    bakery = next(row for row in items if row["code"] == "bakery_goods")
    assert bakery["source"] == "both"
