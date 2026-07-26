"""Общие фикстуры тестов user-service."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
USER_SRC = Path(__file__).resolve().parents[1] / "src"
SITE = Path("/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages")

for p in (REPO_ROOT, USER_SRC, SITE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


@pytest.fixture
def sample_create_request():
    from python.libs.entities.place import PlaceCategory
    from python.libs.entities.user import Gender
    from user_service.entities.common import CreateUserRequest

    return CreateUserRequest(
        name="Алексей",
        gender=Gender.MALE,
        age=28,
        short_bio="Люблю открывать новые места",
        favorite_categories=[PlaceCategory.BARS, PlaceCategory.THEATERS, PlaceCategory.NIGHTCLUBS],
    )
