"""Unit-тесты OOP операций attrs."""

from python.place_service.src.place_service.infra.attr_ops import (
    AndOp,
    BetweenOp,
    ExactMatch,
    NotInOp,
    OrOp,
    compile_attrs_filters,
    parse_attr_predicate,
)
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException
import pytest


def test_exact_scalar():
    op = parse_attr_predicate("has_wifi", True)
    assert isinstance(op, ExactMatch)
    sql, params = op.to_sql("has_wifi", "a0")
    assert "@>" in sql
    assert "true" in params["a0_exact"]


def test_between_open_bounds():
    op = parse_attr_predicate("avg_bill_rub", {"operation": "between", "args": {"from": 200}})
    assert isinstance(op, BetweenOp)
    sql, params = op.to_sql("avg_bill_rub", "a1")
    assert ">=" in sql
    assert "a1_from" in params
    assert "a1_to" not in params


def test_or_list():
    op = parse_attr_predicate(
        "dress_code", {"operation": "or", "args": {"list": ["casual", "smart_casual"]}}
    )
    assert isinstance(op, OrOp)
    sql, _ = op.to_sql("dress_code", "a2")
    assert "?|" in sql


def test_and_list():
    op = parse_attr_predicate("cuisine", {"operation": "and", "args": {"list": ["italian", "vegan"]}})
    assert isinstance(op, AndOp)


def test_not_in_list():
    op = parse_attr_predicate(
        "dress_code", {"operation": "not_in", "args": {"list": ["formal", "black_tie"]}}
    )
    assert isinstance(op, NotInOp)
    sql, params = op.to_sql("dress_code", "a3")
    assert "NOT" in sql
    assert params["a3_nin_sc"] == ["formal", "black_tie"]


def test_nested_forbidden():
    with pytest.raises(CoreException):
        parse_attr_predicate(
            "x",
            {"operation": "or", "args": {"list": [{"operation": "between", "args": {}}]}},
        )


def test_compile_and():
    sql, params = compile_attrs_filters(
        {
            "has_wifi": True,
            "avg_bill_rub": {"operation": "between", "args": {"from": 100, "to": 5000}},
        }
    )
    assert "AND" in sql
    assert len(params) >= 2
