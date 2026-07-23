"""Unit: attrs validation + schedule json."""

from datetime import time

from python.libs.entities.schedule import DaySchedule, TimeInterval, WeeklySchedule
from python.place_service.src.place_service.infra.attrs_validation import validate_attrs
from python.place_service.src.place_service.infra.orm.mappers import schedule_from_json, schedule_to_json
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException
import pytest


def test_validate_attrs_ok():
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"has_wifi": {"type": "boolean"}},
    }
    assert validate_attrs({"has_wifi": True}, schema) == {"has_wifi": True}


def test_validate_attrs_strict_fail():
    schema = {"type": "object", "additionalProperties": False, "properties": {}}
    with pytest.raises(CoreException):
        validate_attrs({"x": 1}, schema)


def test_schedule_roundtrip():
    s = WeeklySchedule(
        timezone="Europe/Moscow",
        periods=[
            DaySchedule(
                weekday=4,
                intervals=[TimeInterval(open=time(18, 0), close=time(2, 0))],
            )
        ],
    )
    raw = schedule_to_json(s)
    back = schedule_from_json(raw)
    assert back is not None
    assert back.timezone == "Europe/Moscow"
    assert back.periods[0].intervals[0].open == time(18, 0)
