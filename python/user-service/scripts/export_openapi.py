"""
Экспорт OpenAPI-схемы FastAPI-приложения без поднятия uvicorn.

Использование (из корня репозитория):
  make openapi-user
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[3]


class CreateUserBody(BaseModel):
    name: str = Field(..., description="Имя")
    age: Optional[int] = Field(None, description="Возраст")
    short_bio: str = Field("", description="Коротко о себе")
    favorite_categories: List[str] = Field(
        default_factory=list,
        description="Коды категорий: bars, cafes, theaters, ...",
    )


class UpdateBioBody(BaseModel):
    long_bio: str = Field(..., description="О себе в свободной форме")


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


class AvatarUploadOut(BaseModel):
    avatar_url: str
    user: UserOut


def build_openapi_app() -> FastAPI:
    """Минимальное FastAPI-приложение со схемами маршрутов для OpenAPI."""
    app = FastAPI(
        title="City Vibe — User Service",
        description="Профили пользователей и онбординг",
        version="1.0.0",
    )

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "service": "user-service"}

    @app.post("/users", tags=["users"], response_model=UserOut, summary="Создать пользователя")
    async def create_user(body: CreateUserBody) -> UserOut:
        raise NotImplementedError

    @app.get("/users/{user_id}", tags=["users"], response_model=UserOut, summary="Получить профиль")
    async def get_user(user_id: int) -> UserOut:
        raise NotImplementedError

    @app.put("/users/{user_id}/bio", tags=["users"], response_model=UserOut, summary="Обновить bio")
    async def update_bio(user_id: int, body: UpdateBioBody) -> UserOut:
        raise NotImplementedError

    @app.post(
        "/users/{user_id}/onboarding/complete",
        tags=["users"],
        response_model=UserOut,
        summary="Завершить онбординг",
    )
    async def complete_onboarding(user_id: int) -> UserOut:
        raise NotImplementedError

    @app.post(
        "/users/{user_id}/avatar",
        tags=["users"],
        response_model=AvatarUploadOut,
        summary="Загрузить аватар",
    )
    async def upload_avatar(user_id: int) -> AvatarUploadOut:
        raise NotImplementedError

    return app


def main() -> None:
    out_dir = REPO_ROOT / "schema"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "user-service.openapi.json"

    app = build_openapi_app()
    schema = app.openapi()
    out_file.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out_file}")


if __name__ == "__main__":
    main()
