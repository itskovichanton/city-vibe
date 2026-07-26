"""Экспорт OpenAPI auth-service."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from python.libs.entities.user import Gender

REPO_ROOT = Path(__file__).resolve().parents[3]


class RegisterBody(BaseModel):
    name: str
    identifier: str
    password: str
    birthdate: Optional[date] = None
    city_id: int
    accept_terms: bool
    gender: Gender


class VerifyBody(BaseModel):
    challenge_id: str
    code: str = Field(..., min_length=6, max_length=6)


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


def build_openapi_app() -> FastAPI:
    app = FastAPI(title="City Vibe — Auth Service", version="1.0.0")

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok"}

    @app.post("/auth/register", response_model=ChallengeOut)
    async def register(body: RegisterBody):
        raise NotImplementedError

    @app.post("/auth/register/verify", response_model=TokensOut)
    async def register_verify(body: VerifyBody):
        raise NotImplementedError

    @app.post("/auth/login", response_model=ChallengeOut)
    async def login(body: RegisterBody):
        raise NotImplementedError

    @app.post("/auth/login/verify", response_model=TokensOut)
    async def login_verify(body: VerifyBody):
        raise NotImplementedError

    return app


def main() -> None:
    out = REPO_ROOT / "schema" / "openapi" / "auth-service.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_openapi_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out}")


if __name__ == "__main__":
    main()
