"""Юнит-тесты маппера ORM → DTO."""

from datetime import datetime, timezone

from user_service.infra.orm.mappers import user_dto_to_response, user_model_to_dto
from user_service.infra.orm.models import UserModel

from python.libs.entities.user import PlaceCategory, Status


def test_user_model_to_dto():
    model = UserModel(
        id=10,
        name="Алексей",
        age=28,
        short_bio="short",
        long_bio="long",
        avatar_url="http://localhost:9000/city-vibe/avatars/1.jpg",
        status="ACTIVE",
        role="REGULAR",
        favorite_categories=["bars", "theaters"],
        onboarding_completed=True,
        deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    dto = user_model_to_dto(model)
    assert dto.id == 10
    assert dto.name == "Алексей"
    assert dto.status == Status.ACTIVE
    assert PlaceCategory.BARS in dto.favorite_categories
    assert dto.onboarding_completed is True

    response = user_dto_to_response(dto)
    assert response.id == 10
    assert response.avatar_url.endswith(".jpg")
