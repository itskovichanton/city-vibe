"""
Агрегированная OpenAPI-схема для Flutter (mobile-facing routes через api-gateway).

Flutter использует ТОЛЬКО schema/openapi/city-vibe-mobile.json
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[3]


class GeoOut(BaseModel):
    latitude: float
    longitude: float


class CityOut(BaseModel):
    id: int
    name: str
    slug: str
    region: str = ""
    geo: Optional[GeoOut] = None
    is_major: bool = True
    sort_order: int = 0
    about: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    distance_m: Optional[float] = Field(
        default=None,
        description="Только для GET /cities/nearest — расстояние в метрах",
    )


class RegisterBody(BaseModel):
    name: str
    identifier: str
    password: str
    birthdate: Optional[date] = None
    city_id: int
    accept_terms: bool


class VerifyBody(BaseModel):
    challenge_id: str
    code: str = Field(..., min_length=6, max_length=6)


class LoginBody(BaseModel):
    identifier: str
    password: str


class ResendBody(BaseModel):
    challenge_id: str


class ForgotBody(BaseModel):
    identifier: str
    channel: Optional[str] = None


class ResetBody(BaseModel):
    reset_token: str
    new_password: str


class RefreshBody(BaseModel):
    refresh_token: str


class GoogleBody(BaseModel):
    id_token: str
    city_id: Optional[int] = None
    name: Optional[str] = None
    birthdate: Optional[date] = None


class ChallengeOut(BaseModel):
    challenge_id: str
    channel: str
    destination_masked: str
    expires_in: int = 300


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: Optional[int] = None
    account_id: Optional[int] = None


class CreateUserBody(BaseModel):
    name: str
    age: Optional[int] = None
    short_bio: str = ""
    favorite_categories: List[str] = Field(default_factory=list)
    city_id: Optional[int] = None
    birthdate: Optional[date] = None
    auth_account_id: Optional[int] = None


class UpdateBioBody(BaseModel):
    long_bio: str


class UserOut(BaseModel):
    id: int
    name: str
    status: str
    short_bio: str = ""
    long_bio: str = ""
    age: Optional[int] = None
    avatar_url: Optional[str] = None
    role: str = "REGULAR"
    favorite_categories: List[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    deleted: bool = False
    city_id: Optional[int] = None
    birthdate: Optional[date] = None
    auth_account_id: Optional[int] = None


class AvatarUploadOut(BaseModel):
    avatar_url: str
    user: UserOut


def build_openapi_app() -> FastAPI:
    app = FastAPI(
        title="City Vibe — Mobile API",
        description="Агрегированная схема auth + users + cities + places + design (через api-gateway)",
        version="1.0.0",
    )

    @app.get("/health", tags=["infra"])
    async def health():
        return {"gateway": "ok", "backends": {}}

    @app.get("/cities", tags=["cities"], response_model=List[CityOut])
    async def list_cities():
        raise NotImplementedError

    @app.get("/cities/nearest", tags=["cities"], response_model=CityOut)
    async def nearest_city(
        lat: float = Query(..., description="Широта GPS"),
        lng: float = Query(..., description="Долгота GPS"),
    ):
        """Ближайший крупный город к координатам (earthdistance)."""
        raise NotImplementedError

    @app.get("/cities/{city_id}", tags=["cities"], response_model=CityOut)
    async def get_city(city_id: int):
        raise NotImplementedError

    @app.get("/categories", tags=["categories"])
    async def list_categories():
        raise NotImplementedError

    @app.get("/attr-schemas/{category_code}", tags=["attrs"])
    async def get_attr_schema(category_code: str):
        raise NotImplementedError

    @app.get("/places", tags=["places"])
    async def list_places(owner_id: Optional[int] = None, category: Optional[str] = None):
        raise NotImplementedError

    @app.post("/places", tags=["places"])
    async def create_place(body: dict):
        raise NotImplementedError

    @app.post(
        "/places/search",
        tags=["places", "search"],
        summary="Многокритериальный поиск мест",
        description=(
            "Обязательны city_id, category. Опционально name, limit=20, page=1, "
            "sort_by=rating|distance (+my_geo), open_at, attrs (exact|between|or|and|not_in). "
            "Для мобильного клиента и ИИ-команд."
        ),
    )
    async def search_places(body: dict):
        raise NotImplementedError

    @app.get("/places/{place_id}", tags=["places"])
    async def get_place(place_id: int):
        raise NotImplementedError

    @app.patch("/places/{place_id}", tags=["places"])
    async def patch_place(place_id: int, body: dict):
        raise NotImplementedError

    @app.delete("/places/{place_id}", tags=["places"])
    async def delete_place(place_id: int):
        raise NotImplementedError

    @app.get("/pin-styles/default", tags=["design"])
    async def default_pin():
        raise NotImplementedError

    @app.get("/chat-themes/default", tags=["design"])
    async def default_theme():
        raise NotImplementedError

    @app.post(
        "/milana/places/search",
        tags=["milana", "places"],
        summary="NL-поиск мест (ИИ-агент Милана)",
        description=(
            "Произвольный русский текст q. Variant B: plan(world) → build(compact schemas) → "
            "places/search × N → message от Миланы. Также: GET /milana/world, /milana/cities, "
            "/milana/categories, /milana/attr-schemas/{code}."
        ),
    )
    async def milana_places_search(body: dict):
        raise NotImplementedError

    @app.get("/milana/world", tags=["milana", "world"], summary="Справочник мира (города+категории)")
    async def milana_world():
        raise NotImplementedError

    @app.get("/milana/cities", tags=["milana", "world"])
    async def milana_cities():
        raise NotImplementedError

    @app.get("/milana/categories", tags=["milana", "world"])
    async def milana_categories():
        raise NotImplementedError

    @app.get("/milana/attr-schemas/{category_code}", tags=["milana", "world"])
    async def milana_attr_schema(category_code: str):
        raise NotImplementedError

    @app.post("/auth/register", tags=["auth"], response_model=ChallengeOut)
    async def register(body: RegisterBody):
        raise NotImplementedError

    @app.post("/auth/register/verify", tags=["auth"], response_model=TokensOut)
    async def register_verify(body: VerifyBody):
        raise NotImplementedError

    @app.post("/auth/login", tags=["auth"], response_model=ChallengeOut)
    async def login(body: LoginBody):
        raise NotImplementedError

    @app.post("/auth/login/verify", tags=["auth"], response_model=TokensOut)
    async def login_verify(body: VerifyBody):
        raise NotImplementedError

    @app.post("/auth/otp/resend", tags=["auth"], response_model=ChallengeOut)
    async def resend_otp(body: ResendBody):
        raise NotImplementedError

    @app.post("/auth/password/forgot", tags=["auth"], response_model=ChallengeOut)
    async def forgot_password(body: ForgotBody):
        raise NotImplementedError

    @app.post("/auth/password/forgot/verify", tags=["auth"])
    async def forgot_verify(body: VerifyBody):
        raise NotImplementedError

    @app.post("/auth/password/reset", tags=["auth"])
    async def reset_password(body: ResetBody):
        raise NotImplementedError

    @app.post("/auth/token/refresh", tags=["auth"], response_model=TokensOut)
    async def refresh_token(body: RefreshBody):
        raise NotImplementedError

    @app.post("/auth/logout", tags=["auth"])
    async def logout(body: RefreshBody):
        raise NotImplementedError

    @app.post("/auth/social/google", tags=["auth"], response_model=TokensOut)
    async def google_auth(body: GoogleBody):
        raise NotImplementedError

    @app.post("/users", tags=["users"], response_model=UserOut)
    async def create_user(body: CreateUserBody):
        raise NotImplementedError

    @app.get("/users/{user_id}", tags=["users"], response_model=UserOut)
    async def get_user(user_id: int):
        raise NotImplementedError

    @app.put("/users/{user_id}/bio", tags=["users"], response_model=UserOut)
    async def update_bio(user_id: int, body: UpdateBioBody):
        raise NotImplementedError

    @app.post("/users/{user_id}/onboarding/complete", tags=["users"], response_model=UserOut)
    async def complete_onboarding(user_id: int):
        raise NotImplementedError

    @app.post("/users/{user_id}/avatar", tags=["users"], response_model=AvatarUploadOut)
    async def upload_avatar(user_id: int):
        raise NotImplementedError

    return app


def main() -> None:
    out = REPO_ROOT / "schema" / "openapi" / "city-vibe-mobile.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_openapi_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out}")
    print("Flutter: используйте schema/openapi/city-vibe-mobile.json")


if __name__ == "__main__":
    main()
