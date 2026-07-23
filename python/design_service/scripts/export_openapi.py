"""Экспорт OpenAPI design-service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[3]


class PinStyleOut(BaseModel):
    id: int
    code: str
    name: str
    image_url: str
    gif_url: Optional[str] = None
    anchor_x: float = 0.5
    anchor_y: float = 1.0


class ChatThemeOut(BaseModel):
    id: int
    code: str
    name: str
    background_url: str
    font_family: str = "system"
    colors: Dict[str, Any] = {}


def build_openapi_app() -> FastAPI:
    app = FastAPI(title="City Vibe — Design Service", version="1.0.0")

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok", "service": "design-service"}

    @app.get("/pin-styles", tags=["pins"], response_model=List[PinStyleOut])
    async def list_pins():
        raise NotImplementedError

    @app.get("/pin-styles/default", tags=["pins"], response_model=PinStyleOut)
    async def default_pin():
        raise NotImplementedError

    @app.get("/pin-styles/{style_id}", tags=["pins"], response_model=PinStyleOut)
    async def get_pin(style_id: int):
        raise NotImplementedError

    @app.get("/chat-themes", tags=["themes"], response_model=List[ChatThemeOut])
    async def list_themes():
        raise NotImplementedError

    @app.get("/chat-themes/default", tags=["themes"], response_model=ChatThemeOut)
    async def default_theme():
        raise NotImplementedError

    @app.get("/chat-themes/{theme_id}", tags=["themes"], response_model=ChatThemeOut)
    async def get_theme(theme_id: int):
        raise NotImplementedError

    return app


def main() -> None:
    out = REPO_ROOT / "schema" / "openapi" / "design-service.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_openapi_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out}")


if __name__ == "__main__":
    main()
