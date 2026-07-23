"""Маппинг ORM ↔ DTO + сериализация schedule."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Optional

from python.libs.entities.city import City
from python.libs.entities.common import Contact, ContactType, Rating
from python.libs.entities.geo import GeoLocation
from python.libs.entities.place import AttrSchema, Place, PlaceCategory, PlaceCategoryInfo
from python.libs.entities.schedule import DaySchedule, ScheduleException, TimeInterval, WeeklySchedule
from python.libs.utils.translit import slugify
from python.place_service.src.place_service.entities.common import CityResponse
from python.place_service.src.place_service.infra.orm.models import (
    AttrSchemaModel,
    CityModel,
    PlaceCategoryModel,
    PlaceModel,
)

__all__ = [
    "slugify",
    "city_model_to_dto",
    "city_dto_to_response",
    "category_model_to_dto",
    "attr_schema_model_to_dto",
    "place_model_to_dto",
    "schedule_to_json",
    "schedule_from_json",
]


def city_model_to_dto(model: CityModel) -> City:
    return City(
        id=model.id,
        deleted=model.deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        name=model.name,
        slug=model.slug,
        about=model.about or "",
        geo=GeoLocation.of(model.lat, model.lng),
        region=model.region or "",
        is_major=model.is_major,
        sort_order=model.sort_order,
    )


def city_dto_to_response(city: City) -> CityResponse:
    return CityResponse(
        id=city.id,
        name=city.name,
        slug=city.slug,
        region=city.region,
        geo=city.geo,
        is_major=city.is_major,
        sort_order=city.sort_order,
        about=city.about,
        deleted=city.deleted,
        created_at=city.created_at,
        updated_at=city.updated_at,
    )


def category_model_to_dto(model: PlaceCategoryModel) -> PlaceCategoryInfo:
    return PlaceCategoryInfo(
        id=model.id,
        deleted=model.deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        code=model.code,
        title=model.title,
        title_en=model.title_en or "",
        icon_url=model.icon_url,
        sort_order=model.sort_order,
        is_active=model.is_active,
    )


def attr_schema_model_to_dto(model: AttrSchemaModel) -> AttrSchema:
    return AttrSchema(
        id=model.id,
        deleted=model.deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        category_code=model.category_code,
        json_schema=dict(model.json_schema or {}),
        version=model.version,
    )


def _parse_time(value: str | time) -> time:
    if isinstance(value, time):
        return value
    parts = str(value).split(":")
    return time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)


def schedule_from_json(raw: Optional[dict[str, Any]]) -> Optional[WeeklySchedule]:
    if not raw:
        return None
    periods = []
    for p in raw.get("periods") or []:
        intervals = [
            TimeInterval(open=_parse_time(i["open"]), close=_parse_time(i["close"]))
            for i in (p.get("intervals") or [])
        ]
        periods.append(
            DaySchedule(weekday=int(p["weekday"]), closed=bool(p.get("closed", False)), intervals=intervals)
        )
    exceptions = []
    for e in raw.get("exceptions") or []:
        intervals = None
        if e.get("intervals"):
            intervals = [
                TimeInterval(open=_parse_time(i["open"]), close=_parse_time(i["close"]))
                for i in e["intervals"]
            ]
        d = e["date"]
        if isinstance(d, str):
            d = date.fromisoformat(d)
        exceptions.append(
            ScheduleException(
                date=d,
                closed=bool(e.get("closed", False)),
                intervals=intervals,
                note=e.get("note"),
            )
        )
    return WeeklySchedule(
        timezone=raw.get("timezone") or "Europe/Moscow",
        periods=periods,
        exceptions=exceptions,
    )


def schedule_to_json(schedule: Optional[WeeklySchedule] | dict[str, Any]) -> Optional[dict[str, Any]]:
    if schedule is None:
        return None
    if isinstance(schedule, dict):
        return schedule

    def _t(t: time) -> str:
        return t.strftime("%H:%M")

    return {
        "timezone": schedule.timezone,
        "periods": [
            {
                "weekday": p.weekday,
                "closed": p.closed,
                "intervals": [{"open": _t(i.open), "close": _t(i.close)} for i in p.intervals],
            }
            for p in schedule.periods
        ],
        "exceptions": [
            {
                "date": e.date.isoformat() if isinstance(e.date, date) else str(e.date),
                "closed": e.closed,
                "intervals": (
                    [{"open": _t(i.open), "close": _t(i.close)} for i in e.intervals]
                    if e.intervals
                    else None
                ),
                "note": e.note,
            }
            for e in schedule.exceptions
        ],
    }


def place_model_to_dto(model: PlaceModel) -> Place:
    contacts: list[Contact] = []
    for c in model.contacts or []:
        try:
            contacts.append(
                Contact(
                    id=int(c.get("id", 0)),
                    deleted=bool(c.get("deleted", False)),
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                    type=ContactType(c["type"]) if not isinstance(c.get("type"), ContactType) else c["type"],
                    value=str(c["value"]),
                    verified=bool(c.get("verified", False)),
                )
            )
        except Exception:
            continue
    return Place(
        id=model.id,
        deleted=model.deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        geo=GeoLocation(latitude=float(model.lat), longitude=float(model.lng)),
        name=model.name,
        about=model.about,
        category=PlaceCategory(model.category_code),
        owner_id=model.owner_id,
        rating=Rating(up_votes=model.rating_up, down_votes=model.rating_down),
        album=None,
        contacts=contacts,
        attrs=dict(model.attrs or {}),
        schedule=schedule_from_json(model.schedule),
        pin_style_id=model.pin_style_id,
        chat_theme_id=model.chat_theme_id,
        city_id=model.city_id,
    )


def place_to_api_dict(place: Place) -> dict[str, Any]:
    return {
        "id": place.id,
        "name": place.name,
        "about": place.about,
        "category": place.category.value if isinstance(place.category, PlaceCategory) else place.category,
        "owner_id": place.owner_id,
        "city_id": place.city_id,
        "geo": {"latitude": place.geo.latitude, "longitude": place.geo.longitude},
        "attrs": place.attrs,
        "schedule": schedule_to_json(place.schedule),
        "pin_style_id": place.pin_style_id,
        "chat_theme_id": place.chat_theme_id,
        "rating": (
            {"up_votes": place.rating.up_votes, "down_votes": place.rating.down_votes}
            if place.rating
            else None
        ),
        "contacts": [
            {"type": c.type.value if hasattr(c.type, "value") else c.type, "value": c.value, "verified": c.verified}
            for c in place.contacts
        ],
        "deleted": place.deleted,
        "created_at": place.created_at.isoformat() if isinstance(place.created_at, datetime) else place.created_at,
        "updated_at": place.updated_at.isoformat() if isinstance(place.updated_at, datetime) else place.updated_at,
    }
