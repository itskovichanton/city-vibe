"""Юнит-тесты сериализации EventBus."""

from dataclasses import dataclass
from datetime import datetime

from python.libs.clients.infra.events.eventbus import serialize_message, deserialize_message
from python.libs.entities.place import PlaceCategory
from python.libs.entities.user import Status, User, UserRole


@dataclass
class _Dummy:
    x: int
    y: str


def test_serialize_dataclass_roundtrip():
    raw = serialize_message(_Dummy(x=1, y="привет"))
    data = deserialize_message(raw)
    assert data == {"x": 1, "y": "привет"}


def test_serialize_user_event_payload():
    user = User(
        id=1,
        deleted=False,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
        status=Status.ACTIVE,
        name="Алексей",
        short_bio="bio",
        favorite_categories=[PlaceCategory.BARS],
        role=UserRole.REGULAR,
    )
    raw = serialize_message(user)
    data = deserialize_message(raw)
    assert data["name"] == "Алексей"
    assert data["favorite_categories"] == ["bars"]


def test_serialize_bytes_passthrough():
    assert serialize_message(b"abc") == b"abc"
