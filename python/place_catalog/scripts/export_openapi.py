"""Экспорт OpenAPI place-catalog."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

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


def build_openapi_app() -> FastAPI:
    app = FastAPI(title="City Vibe — Place Catalog", version="1.0.0")

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok"}

    @app.get("/cities", tags=["cities"], response_model=List[CityOut])
    async def list_cities():
        raise NotImplementedError

    @app.get("/cities/{city_id}", tags=["cities"], response_model=CityOut)
    async def get_city(city_id: int):
        raise NotImplementedError

    return app


def main() -> None:
    out = REPO_ROOT / "schema" / "openapi" / "place-catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_openapi_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out}")


if __name__ == "__main__":
    main()
