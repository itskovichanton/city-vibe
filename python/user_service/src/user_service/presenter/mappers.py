"""Маппинг HTTP-моделей → DTO use-case (тонкий presenter-слой)."""

from __future__ import annotations

from python.libs.entities.place import PlaceCategory
from python.user_service.src.user_service.entities.common import (
    CompleteOnboardingRequest,
    CreateUserRequest,
    DeleteUserRequest,
    UpdateBioRequest,
    UpdateProfileRequest,
    UploadAvatarRequest,
)


def parse_category_codes(codes: list[str] | None) -> list[PlaceCategory] | None:
    if codes is None:
        return None
    parsed: list[PlaceCategory] = []
    for code in codes:
        try:
            parsed.append(PlaceCategory(code))
        except ValueError:
            continue
    return parsed


def to_create_user_request(body) -> CreateUserRequest:
    return CreateUserRequest(
        name=body.name,
        gender=body.gender,
        age=body.age,
        short_bio=body.short_bio,
        favorite_categories=parse_category_codes(body.favorite_categories) or [],
        city_id=body.city_id,
        birthdate=body.birthdate,
        auth_account_id=body.auth_account_id,
    )


def to_update_profile_request(user_id: int, body) -> UpdateProfileRequest:
    return UpdateProfileRequest(
        user_id=user_id,
        name=body.name,
        favorite_categories=parse_category_codes(body.favorite_categories),
    )


def to_update_bio_request(user_id: int, body) -> UpdateBioRequest:
    return UpdateBioRequest(user_id=user_id, long_bio=body.long_bio)


def to_complete_onboarding_request(user_id: int) -> CompleteOnboardingRequest:
    return CompleteOnboardingRequest(user_id=user_id)


def to_delete_user_request(user_id: int) -> DeleteUserRequest:
    return DeleteUserRequest(user_id=user_id)


def to_upload_avatar_request(
    user_id: int,
    *,
    data: bytes,
    content_type: str,
    extension: str,
) -> UploadAvatarRequest:
    return UploadAvatarRequest(
        user_id=user_id,
        data=data,
        content_type=content_type,
        extension=extension,
    )
