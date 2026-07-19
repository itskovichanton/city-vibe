"""Маппинг ORM ↔ доменные DTO. Репозитории отдают только DTO."""

from python.libs.entities.user import PlaceCategory, Status, User, UserRole
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


def user_model_to_dto(model: UserModel) -> User:
    """ORM → доменный User (shared entity)."""
    return User(
        id=model.id,
        deleted=model.deleted,
        created_at=model.created_at,
        updated_at=model.updated_at,
        status=Status[model.status] if model.status in Status.__members__ else Status.ACTIVE,
        name=model.name,
        short_bio=model.short_bio or "",
        long_bio=model.long_bio or "",
        age=model.age,
        username=model.username,
        avatar_url=model.avatar_url,
        role=UserRole[model.role] if model.role in UserRole.__members__ else UserRole.REGULAR,
        favorite_categories=_parse_categories(model.favorite_categories),
        onboarding_completed=model.onboarding_completed,
    )


def user_dto_to_response(user: User) -> UserResponse:
    """Доменный User → ответ API."""
    return UserResponse(
        id=user.id,
        name=user.name,
        status=user.status,
        short_bio=user.short_bio,
        long_bio=user.long_bio,
        age=user.age,
        avatar_url=user.avatar_url,
        role=user.role,
        favorite_categories=list(user.favorite_categories),
        onboarding_completed=user.onboarding_completed,
        deleted=user.deleted,
    )
