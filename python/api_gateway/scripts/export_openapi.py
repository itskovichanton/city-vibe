"""Экспорт OpenAPI api-gateway."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_openapi_app() -> FastAPI:
    app = FastAPI(title="City Vibe — API Gateway", version="1.0.0")

    @app.get("/health", tags=["infra"])
    async def health():
        return {"gateway": "ok", "backends": {}}

    return app


def main() -> None:
    out = REPO_ROOT / "schema" / "openapi" / "api-gateway.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_openapi_app().openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OpenAPI сохранён: {out}")


if __name__ == "__main__":
    main()
