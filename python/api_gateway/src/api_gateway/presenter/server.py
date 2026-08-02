"""Reverse proxy FastAPI + опциональная JWT-валидация."""

from __future__ import annotations

import logging
from typing import Optional

import httpx
import jwt
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.infra import CityVibeInfraSupport

logger = logging.getLogger(__name__)


@bean(
    port=("server.port", int, 8080),
    host=("server.host", str, "0.0.0.0"),
    auth_url=("upstreams.auth", str, "http://localhost:8082"),
    users_url=("upstreams.users", str, "http://localhost:8081"),
    places_url=("upstreams.places", str, "http://localhost:8083"),
    design_url=("upstreams.design", str, "http://localhost:8085"),
    milana_url=("upstreams.milana", str, "http://localhost:8086"),
    jwt_secret=("auth.jwt_secret", str, "dev-jwt-secret-change-me"),
)
class Server:
    config_service: ConfigService
    infra_support: CityVibeInfraSupport
    _client: httpx.AsyncClient | None = None

    def init(self, **kwargs):
        self.port = kwargs.get("port", getattr(self, "port", 8080))
        self.host = kwargs.get("host", getattr(self, "host", "0.0.0.0"))
        self._auth_url = kwargs.get("auth_url", "http://localhost:8082").rstrip("/")
        self._users_url = kwargs.get("users_url", "http://localhost:8081").rstrip("/")
        self._places_url = kwargs.get("places_url", "http://localhost:8083").rstrip("/")
        self._design_url = kwargs.get("design_url", "http://localhost:8085").rstrip("/")
        self._milana_url = kwargs.get("milana_url", "http://localhost:8086").rstrip("/")
        self._jwt_secret = kwargs.get("jwt_secret", "dev-jwt-secret-change-me")
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        app = FastAPI(title="City Vibe — API Gateway", version="1.0.0")
        self.infra_support.mount(app)

        @app.on_event("startup")
        async def _startup():
            # 60s default; milana (LLM) может идти дольше — отдельный timeout на route
            self._client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)

        @app.on_event("shutdown")
        async def _shutdown():
            if self._client:
                await self._client.aclose()

        return app

    def _validate_jwt_optional(self, request: Request) -> Optional[JSONResponse]:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:]
        try:
            jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
        except jwt.PyJWTError:
            return JSONResponse(status_code=401, content={"error": "invalid_token"})
        return None

    async def _proxy(
        self,
        request: Request,
        base_url: str,
        path: str,
        *,
        timeout: float | None = None,
    ) -> Response:
        assert self._client is not None
        url = f"{base_url}{path}"
        if request.url.query:
            url = f"{url}?{request.url.query}"
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}
        body = await request.body()
        kwargs: dict = {"headers": headers, "content": body}
        if timeout is not None:
            kwargs["timeout"] = timeout
        resp = await self._client.request(request.method, url, **kwargs)
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            assert self._client is not None
            backends = {
                "auth": f"{self._auth_url}/health",
                "users": f"{self._users_url}/health",
                "places": f"{self._places_url}/health",
                "design": f"{self._design_url}/health",
                "milana": f"{self._milana_url}/health",
            }
            status = {"gateway": "ok", "backends": {}}
            for name, url in backends.items():
                try:
                    r = await self._client.get(url, timeout=3.0)
                    status["backends"][name] = "ok" if r.status_code < 500 else "error"
                except Exception as e:
                    status["backends"][name] = f"down: {e}"
            return status

        @self.fast_api.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy_auth(request: Request, path: str):
            err = self._validate_jwt_optional(request)
            if err:
                return err
            return await self._proxy(request, self._auth_url, f"/auth/{path}")

        @self.fast_api.api_route("/media/{path:path}", methods=["GET", "HEAD"])
        async def proxy_media(request: Request, path: str):
            return await self._proxy(request, self._users_url, f"/media/{path}")

        @self.fast_api.api_route("/users", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy_users_root(request: Request):
            err = self._validate_jwt_optional(request)
            if err:
                return err
            return await self._proxy(request, self._users_url, "/users")

        @self.fast_api.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy_users(request: Request, path: str):
            err = self._validate_jwt_optional(request)
            if err:
                return err
            return await self._proxy(request, self._users_url, f"/users/{path}")

        # place-service
        @self.fast_api.get("/cities")
        async def proxy_cities_root(request: Request):
            return await self._proxy(request, self._places_url, "/cities")

        @self.fast_api.api_route("/cities/{path:path}", methods=["GET"])
        async def proxy_cities(request: Request, path: str):
            return await self._proxy(request, self._places_url, f"/cities/{path}")

        @self.fast_api.get("/categories")
        async def proxy_categories(request: Request):
            return await self._proxy(request, self._places_url, "/categories")

        @self.fast_api.api_route("/attr-schemas", methods=["GET"])
        async def proxy_attr_schemas_root(request: Request):
            return await self._proxy(request, self._places_url, "/attr-schemas")

        @self.fast_api.api_route("/attr-schemas/{path:path}", methods=["GET"])
        async def proxy_attr_schemas(request: Request, path: str):
            return await self._proxy(request, self._places_url, f"/attr-schemas/{path}")

        @self.fast_api.api_route("/places", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy_places_root(request: Request):
            err = self._validate_jwt_optional(request)
            if err:
                return err
            return await self._proxy(request, self._places_url, "/places")

        @self.fast_api.api_route("/places/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy_places(request: Request, path: str):
            err = self._validate_jwt_optional(request)
            if err:
                return err
            return await self._proxy(request, self._places_url, f"/places/{path}")

        # design-service
        @self.fast_api.api_route("/pin-styles", methods=["GET"])
        async def proxy_pins_root(request: Request):
            return await self._proxy(request, self._design_url, "/pin-styles")

        @self.fast_api.api_route("/pin-styles/{path:path}", methods=["GET"])
        async def proxy_pins(request: Request, path: str):
            return await self._proxy(request, self._design_url, f"/pin-styles/{path}")

        @self.fast_api.api_route("/chat-themes", methods=["GET"])
        async def proxy_themes_root(request: Request):
            return await self._proxy(request, self._design_url, "/chat-themes")

        @self.fast_api.api_route("/chat-themes/{path:path}", methods=["GET"])
        async def proxy_themes(request: Request, path: str):
            return await self._proxy(request, self._design_url, f"/chat-themes/{path}")

        # milana-service (LLM — длинный timeout)
        @self.fast_api.api_route("/milana", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy_milana_root(request: Request):
            return await self._proxy(request, self._milana_url, "/milana", timeout=120.0)

        @self.fast_api.api_route("/milana/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
        async def proxy_milana(request: Request, path: str):
            return await self._proxy(
                request, self._milana_url, f"/milana/{path}", timeout=120.0
            )
