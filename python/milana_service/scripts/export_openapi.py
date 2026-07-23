"""Экспорт OpenAPI milana-service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[3]


class MilanaGeo(BaseModel):
    lat: float
    lng: float


class MilanaPlacesSearchIn(BaseModel):
    q: str = Field(..., description="Произвольный текст пожеланий на русском")
    city_id: Optional[int] = Field(None, description="ID города (default из config)")
    my_geo: Optional[MilanaGeo] = None
    weekday: Optional[int] = Field(None, ge=0, le=6)
    limit_per_step: Optional[int] = Field(None, ge=1, le=20)


class MilanaPlanStepOut(BaseModel):
    intent: str
    category: str
    why: str = ""


class MilanaStepOut(BaseModel):
    intent: str
    why: str = ""
    search: Dict[str, Any]
    total: int = 0
    places: List[Dict[str, Any]] = []


class MilanaPlacesSearchOut(BaseModel):
    message: str = Field(..., description="Текст от Миланы")
    steps: List[MilanaStepOut]
    plan: List[MilanaPlanStepOut] = []
    model: Optional[str] = None
    used_llm: bool = True


def build_openapi_app() -> FastAPI:
    app = FastAPI(
        title="City Vibe — Milana Service",
        description="ИИ-агент Милана: NL → places/search (DeepSeek, variant B)",
        version="1.1.0",
    )

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "service": "milana-service"}

    @app.get("/milana/world", tags=["world"], summary="Города + категории (compact)")
    async def world():
        raise NotImplementedError

    @app.get("/milana/cities", tags=["world"], summary="Города compact")
    async def cities():
        raise NotImplementedError

    @app.get("/milana/categories", tags=["world"], summary="Категории compact")
    async def categories():
        raise NotImplementedError

    @app.get(
        "/milana/attr-schemas/{category_code}",
        tags=["world"],
        summary="Compact JSON Schema attrs",
    )
    async def attr_schema(category_code: str):
        raise NotImplementedError

    @app.post(
        "/milana/places/search",
        tags=["milana"],
        summary="NL-поиск мест (Милана, variant B)",
        response_model=MilanaPlacesSearchOut,
        description=(
            "Pass1 plan (cities+categories) → Pass2 build (compact schemas) → "
            "places/search × N → message от Миланы. Нужен DEEPSEEK_API_KEY. "
            "Лог: milana-agent-*.txt через LoggerService."
        ),
    )
    async def milana_places_search(body: MilanaPlacesSearchIn):
        raise NotImplementedError

    return app


def main() -> None:
    out = REPO_ROOT / "schema" / "openapi" / "milana-service.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_openapi_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out}")


if __name__ == "__main__":
    main()
