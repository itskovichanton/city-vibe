"""HTTP-клиент place-service: search + справочники мира."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx
from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.libs.utils.schema_compact import compact_json_schema


@bean(base_url=("clients.place_service.url", str, "http://localhost:8083"))
class PlaceSearchHttpClient:
    logger_service: LoggerService

    def init(self, **kwargs):
        self.base_url = (kwargs.get("base_url") or "http://localhost:8083").rstrip("/")
        self._flog = self.logger_service.get_file_logger("milana-agent", max_line_len=80000)

    def _log(self, event: str, **payload: Any) -> None:
        try:
            self._flog.info(json.dumps({"event": event, **payload}, ensure_ascii=False, default=str))
        except Exception:
            self._flog.info(f"{event}: {payload!r}")

    async def _get_json(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            self._log("place_api_get", url=url, status=resp.status_code, body_preview=resp.text[:2000])
            if resp.status_code >= 400:
                raise CoreException(message=f"GET {path} HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
        return data.get("result", data) if isinstance(data, dict) else data

    async def search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/places/search"
        self._log("place_search_request", body=body)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body)
            self._log(
                "place_search_response",
                status=resp.status_code,
                body_preview=resp.text[:4000],
            )
            if resp.status_code >= 400:
                raise CoreException(
                    message=f"places/search HTTP {resp.status_code}: {resp.text[:300]}",
                )
            data = resp.json()
        payload = data.get("result", data) if isinstance(data, dict) else data
        if not isinstance(payload, dict):
            raise CoreException(message="Неожиданный ответ places/search")
        return payload

    async def list_cities_compact(self) -> List[Dict[str, Any]]:
        raw = await self._get_json("/cities")
        items = raw if isinstance(raw, list) else []
        out: List[Dict[str, Any]] = []
        for c in items:
            if not isinstance(c, dict):
                continue
            geo = c.get("geo") or {}
            out.append(
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "slug": c.get("slug"),
                    "region": c.get("region"),
                    "lat": geo.get("latitude") if isinstance(geo, dict) else c.get("lat"),
                    "lng": geo.get("longitude") if isinstance(geo, dict) else c.get("lng"),
                }
            )
        return out

    async def list_categories_compact(self) -> List[Dict[str, Any]]:
        raw = await self._get_json("/categories")
        items = raw if isinstance(raw, list) else []
        out: List[Dict[str, Any]] = []
        for c in items:
            if not isinstance(c, dict):
                continue
            out.append(
                {
                    "code": c.get("code"),
                    "title": c.get("title"),
                    "title_en": c.get("title_en"),
                }
            )
        return out

    async def get_attr_schema_compact(self, category_code: str) -> Dict[str, Any]:
        raw = await self._get_json(f"/attr-schemas/{category_code}")
        if not isinstance(raw, dict):
            raise CoreException(message=f"Schema для {category_code} не найдена")
        schema = raw.get("json_schema") or {}
        return {
            "category_code": raw.get("category_code") or category_code,
            "version": raw.get("version"),
            "json_schema": compact_json_schema(schema if isinstance(schema, dict) else {}),
        }

    async def get_attr_schemas_compact(self, codes: List[str]) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for code in codes:
            if not code or code in result:
                continue
            try:
                result[code] = await self.get_attr_schema_compact(code)
            except Exception as e:
                self._log("attr_schema_miss", category=code, error=str(e))
        return result

    @staticmethod
    def slim_places(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for it in (items or [])[:limit]:
            if not isinstance(it, dict):
                continue
            out.append(
                {
                    "id": it.get("id"),
                    "name": it.get("name"),
                    "about": it.get("about"),
                    "category": it.get("category") or it.get("category_code"),
                    "lat": it.get("lat"),
                    "lng": it.get("lng"),
                    "distance_m": it.get("distance_m"),
                    "attrs": it.get("attrs") or {},
                    "contacts": it.get("contacts"),
                    "rating_up": it.get("rating_up"),
                    "rating_down": it.get("rating_down"),
                }
            )
        return out
