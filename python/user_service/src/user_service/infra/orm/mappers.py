"""Маппинг ORM ↔ доменные DTO. Репозитории отдают только DTO."""

from datetime import date

from python.libs.entities.place import PlaceCategory
from python.libs.entities.user import Gender, Status, User, UserRole
from python.user_service.src.user_service.entities.common import UserResponse
from python.user_service.src.user_service.infra.orm.models import UserModel


def _parse_categories(raw: list[str] | None) -> list[PlaceCategory]:
    if not raw:
        return []
    result: list[PlaceCategory] = []
    for code in raw:
        try:
            result.append(PlaceCategory(code))
        except ValueError:
            # Неизвестная категория из БД — пропускаем, не валим весь профиль
            continue
    return result


def _coerce_gender(raw: Gender | str | None) -> Gender:
    if isinstance(raw, Gender):
        return raw
    if isinstance(raw, str):
        try:
            return Gender(raw)
        except ValueError:
            pass
    return Gender.MALE


def user_model_to_dto(model: UserModel) -> User:
    """ORM → доменный User (shared entity)."""
    return User(
        id=model.id,
        deleted=model.deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        status=Status[model.status] if model.status in Status.__members__ else Status.ACTIVE,
        name=model.name,
        gender=_coerce_gender(model.gender),
        short_bio=model.short_bio or "",
        long_bio=model.long_bio or "",
        age=model.age,
        username=model.username,
        avatar_url=model.avatar_url,
        role=UserRole[model.role] if model.role in UserRole.__members__ else UserRole.REGULAR,
        city_id=model.city_id,
        auth_account_id=model.auth_account_id,
        favorite_categories=_parse_categories(model.favorite_categories),
        onboarding_completed=model.onboarding_completed,
        birthdate=model.birthdate,
    )


def user_dto_to_response(user: User) -> UserResponse:
    """Доменный User → ответ API."""
    return UserResponse(
        id=user.id,
        name=user.name,
        status=user.status,
        gender=user.gender,
        short_bio=user.short_bio,
        long_bio=user.long_bio,
        age=user.age,
        avatar_url=user.avatar_url,
        role=user.role,
        favorite_categories=list(user.favorite_categories),
        onboarding_completed=user.onboarding_completed,
        deleted=user.deleted,
        city_id=user.city_id,
        birthdate=user.birthdate if isinstance(user.birthdate, date) else (
            user.birthdate.date() if user.birthdate else None
        ),
        auth_account_id=user.auth_account_id,
    )
