"""Агент вариант B: PLAN → compact schemas → BUILD → places/products search → MESSAGE."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.milana_service.src.milana_service.agent import prompts
from python.milana_service.src.milana_service.entities.request import (
    MilanaPlacesSearchRequest,
    MilanaPlacesSearchResponse,
    MilanaPlanStep,
    MilanaSearchStepResult,
)
from python.milana_service.src.milana_service.infra.deepseek import DeepSeekClient
from python.milana_service.src.milana_service.infra.place_search_client import PlaceSearchHttpClient
from python.place_service.src.place_service.entities.search import PlaceSearchRequest, ProductSearchRequest


@bean(
    default_city_id=("milana.default_city_id", int, 3),
    places_per_step=("milana.places_per_step", int, 5),
    max_steps=("milana.max_steps", int, 5),
)
class PlacesNlSearchAgent:
    deepseek: DeepSeekClient
    places: PlaceSearchHttpClient
    logger_service: LoggerService

    def init(self, **kwargs):
        self.default_city_id = int(kwargs.get("default_city_id") or 3)
        self.places_per_step = int(kwargs.get("places_per_step") or 5)
        self.max_steps = int(kwargs.get("max_steps") or 5)
        self._flog = self.logger_service.get_file_logger("milana-agent", max_line_len=80000)

    def _log(self, event: str, **payload: Any) -> None:
        try:
            self._flog.info(json.dumps({"event": event, **payload}, ensure_ascii=False, default=str))
        except Exception:
            self._flog.info(f"{event}: {payload!r}")

    async def world_digest(self) -> Dict[str, Any]:
        cities = await self.places.list_cities_compact()
        categories = await self.places.list_categories_compact()
        product_categories = await self.places.list_product_categories_compact()
        return {
            "cities": cities,
            "categories": categories,
            "product_categories": product_categories,
        }

    async def run(self, req: MilanaPlacesSearchRequest) -> MilanaPlacesSearchResponse:
        if not self.deepseek.configured:
            raise CoreException(
                message="DEEPSEEK_API_KEY не задан — Milana не может планировать поиск без LLM",
            )

        city_id = req.city_id if req.city_id is not None else self.default_city_id
        per_step = req.limit_per_step or self.places_per_step
        my_geo = req.my_geo.model_dump() if req.my_geo else None
        weekday = req.weekday if req.weekday is not None else datetime.now().weekday()
        timezone = req.timezone

        self._log(
            "milana_run_start",
            q=req.q,
            city_id=city_id,
            my_geo=my_geo,
            weekday=weekday,
            timezone=timezone,
            limit_per_step=per_step,
        )

        cities = await self.places.list_cities_compact()
        categories = await self.places.list_categories_compact()
        product_categories = await self.places.list_product_categories_compact()
        known_place_codes = {c["code"] for c in categories if c.get("code")}
        known_product_codes = {c["code"] for c in product_categories if c.get("code")}
        self._log(
            "world_loaded",
            cities_n=len(cities),
            categories_n=len(categories),
            product_categories_n=len(product_categories),
        )

        plan_raw = await self.deepseek.chat_json(
            phase="plan",
            system=prompts.PLAN_SYSTEM,
            user=prompts.plan_user_payload(
                q=req.q,
                cities=cities,
                categories=categories,
                product_categories=product_categories,
                city_id=city_id,
                my_geo=my_geo,
                weekday=weekday,
                timezone=timezone,
            ),
            max_tokens=min(2048, self.deepseek.max_tokens),
        )
        plan_steps = self._parse_plan(
            plan_raw,
            known_place_codes=known_place_codes,
            known_product_codes=known_product_codes,
        )[: self.max_steps]
        if not plan_steps:
            raise CoreException(message="Милана не смогла построить план поиска по запросу")
        self._log("plan_ready", plan=plan_steps)

        place_codes = [
            s["category"] for s in plan_steps if s.get("domain") != "product" and s.get("category")
        ]
        schemas = await self.places.get_attr_schemas_compact(place_codes)
        self._log("schemas_loaded", categories=list(schemas.keys()))

        build_raw = await self.deepseek.chat_json(
            phase="build",
            system=prompts.BUILD_SYSTEM,
            user=prompts.build_user_payload(
                q=req.q,
                plan_steps=plan_steps,
                schemas=schemas,
                city_id=city_id,
                my_geo=my_geo,
                weekday=weekday,
                limit=per_step,
                timezone=timezone,
            ),
            max_tokens=min(4096, self.deepseek.max_tokens),
        )
        built = self._parse_build(build_raw, plan_steps=plan_steps)[: self.max_steps]
        if not built:
            raise CoreException(message="Милана не смогла собрать тела поиска")
        self._log("build_ready", steps=[{"intent": b["intent"], "search": b["search"]} for b in built])

        step_results: List[MilanaSearchStepResult] = []
        seen_place_ids: List[int] = []
        seen_product_ids: List[int] = []
        for item in built:
            domain = item.get("domain") or "place"
            search_body = self._normalize_search(
                item["search"],
                city_id=city_id,
                my_geo=my_geo,
                limit=per_step,
                domain=domain,
                timezone=timezone,
            )
            self._apply_excludes(
                search_body,
                domain=domain,
                place_ids=seen_place_ids,
                product_ids=seen_product_ids,
            )
            if domain == "product":
                resolved = await self._resolve_place_name(search_body, city_id=city_id)
                if resolved is False:
                    self._log("place_resolve_miss", intent=item["intent"], body=search_body)
                    step_results.append(
                        MilanaSearchStepResult(
                            domain=domain,
                            intent=item["intent"],
                            why=item.get("why") or "",
                            search=search_body,
                            total=0,
                            places=[],
                            products=[],
                        )
                    )
                    continue
            model = ProductSearchRequest if domain == "product" else PlaceSearchRequest
            try:
                model.model_validate(search_body)
            except Exception as e:
                self._log("search_validation_fail", intent=item["intent"], error=str(e), body=search_body)
                continue
            try:
                if domain == "product":
                    raw = await self.places.search_products(search_body)
                else:
                    raw = await self.places.search(search_body)
            except Exception as e:
                self._log("search_exec_fail", intent=item["intent"], error=str(e))
                step_results.append(
                    MilanaSearchStepResult(
                        domain=domain,
                        intent=item["intent"],
                        why=item.get("why") or "",
                        search=search_body,
                        total=0,
                        places=[],
                        products=[],
                    )
                )
                continue
            items = raw.get("items") or []
            total = int(raw.get("total") or len(items))
            slim_places = [] if domain == "product" else self.places.slim_places(items, per_step)
            slim_products = self.places.slim_products(items, per_step) if domain == "product" else []
            self._collect_seen_ids(
                seen_place_ids,
                seen_product_ids,
                domain=domain,
                places=slim_places,
                products=slim_products,
            )
            step_results.append(
                MilanaSearchStepResult(
                    domain=domain,
                    intent=item["intent"],
                    why=item.get("why") or "",
                    search=search_body,
                    total=total,
                    places=slim_places,
                    products=slim_products,
                )
            )

        if not step_results:
            raise CoreException(message="Все шаги поиска отклонены валидацией")

        message = await self._compose_message(req.q, step_results)
        self._log("milana_run_done", steps_n=len(step_results), message_preview=message[:500])

        return MilanaPlacesSearchResponse(
            message=message,
            steps=step_results,
            plan=[MilanaPlanStep(**s) for s in plan_steps],
            model=self.deepseek.model,
            used_llm=True,
        )

    def _parse_plan(
        self,
        data: Dict[str, Any],
        *,
        known_place_codes: set,
        known_product_codes: set,
    ) -> List[Dict[str, Any]]:
        steps_raw = data.get("steps")
        if not isinstance(steps_raw, list):
            raise CoreException(message="План LLM: нет массива steps")
        out: List[Dict[str, Any]] = []
        for s in steps_raw:
            if not isinstance(s, dict):
                continue
            cat = str(s.get("category") or "").strip()
            place_name = str(s.get("place_name") or "").strip() or None
            place_category = str(s.get("place_category") or "").strip() or None
            if place_category and known_place_codes and place_category not in known_place_codes:
                place_category = None
            domain = str(s.get("domain") or "").strip().lower()
            if domain not in ("place", "product"):
                if cat in known_place_codes:
                    domain = "place"
                elif cat in known_product_codes:
                    domain = "product"
                elif place_name:
                    domain = "product"
                else:
                    self._log("plan_skip_unknown_category", step=s)
                    continue
            if not cat:
                if not (domain == "product" and place_name):
                    self._log("plan_skip_unknown_category", step=s)
                    continue
            else:
                allowed = known_product_codes if domain == "product" else known_place_codes
                if allowed and cat not in allowed:
                    self._log("plan_skip_unknown_category", step=s)
                    continue
            out.append(
                {
                    "domain": domain,
                    "intent": str(s.get("intent") or cat or place_name or "поиск").strip(),
                    "category": cat,
                    "why": str(s.get("why") or "").strip(),
                    "place_name": place_name,
                    "place_category": place_category,
                }
            )
        return out

    def _parse_build(
        self,
        data: Dict[str, Any],
        *,
        plan_steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        steps_raw = data.get("steps")
        if not isinstance(steps_raw, list):
            raise CoreException(message="Build LLM: нет массива steps")
        out: List[Dict[str, Any]] = []
        for i, s in enumerate(steps_raw):
            if not isinstance(s, dict):
                continue
            search = s.get("search")
            if not isinstance(search, dict):
                continue
            plan = plan_steps[i] if i < len(plan_steps) else {}
            domain = str(s.get("domain") or plan.get("domain") or "place").strip().lower()
            if domain not in ("place", "product"):
                domain = "place"
            if domain == "product":
                if plan.get("place_name") and not search.get("place_name") and not search.get("place_id"):
                    search["place_name"] = plan["place_name"]
                if plan.get("place_category") and not search.get("place_category"):
                    search["place_category"] = plan["place_category"]
                if plan.get("category") and not search.get("category"):
                    search["category"] = plan["category"]
            elif plan.get("place_name") and not search.get("name"):
                search["name"] = plan["place_name"]
            out.append(
                {
                    "domain": domain,
                    "intent": str(s.get("intent") or plan.get("intent") or "поиск").strip(),
                    "why": str(s.get("why") or plan.get("why") or "").strip(),
                    "search": search,
                }
            )
        return out

    def _normalize_search(
        self,
        body: Dict[str, Any],
        *,
        city_id: int,
        my_geo: Optional[dict],
        limit: int,
        domain: str = "place",
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        b = dict(body)
        b.setdefault("city_id", city_id)
        b.setdefault("limit", limit)
        b.setdefault("page", 1)
        if timezone and not b.get("timezone"):
            b["timezone"] = timezone
        if my_geo and not b.get("my_geo"):
            b["my_geo"] = my_geo
        if b.get("sort_by") == "distance" and not b.get("my_geo") and my_geo:
            b["my_geo"] = my_geo
        if b.get("sort_by") == "distance" and not b.get("my_geo"):
            b.pop("sort_by", None)
        if my_geo and not b.get("sort_by"):
            b["sort_by"] = "distance"
        if domain == "product":
            b.pop("attrs", None)
            if not b.get("q") and b.get("name"):
                b["q"] = b["name"]
            b.pop("name", None)
            if b.get("sort_by") == "rating":
                b.pop("sort_by", None)
                if my_geo:
                    b["sort_by"] = "distance"
            if not b.get("place_id"):
                b.setdefault("one_per_place", True)
        return b

    @staticmethod
    def _merge_ids(existing: Any, extra: List[int], *, limit: int = 200) -> List[int]:
        out: List[int] = []
        seen: set[int] = set()
        for raw in list(existing or []) + extra:
            try:
                n = int(raw)
            except (TypeError, ValueError):
                continue
            if n <= 0 or n in seen:
                continue
            seen.add(n)
            out.append(n)
            if len(out) >= limit:
                break
        return out

    def _apply_excludes(
        self,
        body: Dict[str, Any],
        *,
        domain: str,
        place_ids: List[int],
        product_ids: List[int],
    ) -> None:
        if domain == "product":
            merged = self._merge_ids(body.get("exclude_ids"), product_ids)
            if merged:
                body["exclude_ids"] = merged
            merged_pl = self._merge_ids(body.get("exclude_place_ids"), place_ids)
            if merged_pl:
                body["exclude_place_ids"] = merged_pl
        else:
            merged = self._merge_ids(body.get("exclude_ids"), place_ids)
            if merged:
                body["exclude_ids"] = merged

    @staticmethod
    def _collect_seen_ids(
        place_ids: List[int],
        product_ids: List[int],
        *,
        domain: str,
        places: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
    ) -> None:
        if domain == "product":
            for row in products:
                try:
                    pid = int(row.get("id"))
                except (TypeError, ValueError):
                    pid = 0
                if pid > 0:
                    product_ids.append(pid)
                place = row.get("place") if isinstance(row.get("place"), dict) else {}
                raw = row.get("place_id") or place.get("id")
                try:
                    plid = int(raw)
                except (TypeError, ValueError):
                    plid = 0
                if plid > 0:
                    place_ids.append(plid)
        else:
            for row in places:
                try:
                    plid = int(row.get("id"))
                except (TypeError, ValueError):
                    plid = 0
                if plid > 0:
                    place_ids.append(plid)

    async def _resolve_place_name(self, body: Dict[str, Any], *, city_id: int) -> Optional[bool]:
        """Резолв place_name → place_id. False = места нет (шаг пустой). None = нечего резолвить."""
        place_name = str(body.get("place_name") or "").strip()
        if not place_name or body.get("place_id"):
            return None
        lookup: Dict[str, Any] = {
            "city_id": body.get("city_id") or city_id,
            "name": place_name,
            "limit": 1,
            "page": 1,
        }
        place_cat = str(body.get("place_category") or "").strip()
        if place_cat:
            lookup["category"] = place_cat
        try:
            raw = await self.places.search(lookup)
        except Exception as e:
            self._log("place_resolve_fail", error=str(e), lookup=lookup)
            return False
        items = raw.get("items") or []
        first = items[0] if items and isinstance(items[0], dict) else None
        pid = first.get("id") if first else None
        if not pid:
            return False
        body["place_id"] = int(pid)
        body.pop("place_name", None)
        body.pop("one_per_place", None)
        return True

    async def _compose_message(self, q: str, steps: List[MilanaSearchStepResult]) -> str:
        payload = []
        for s in steps:
            step: Dict[str, Any] = {
                "domain": s.domain,
                "intent": s.intent,
                "why": s.why,
                "total": s.total,
                "places": [
                    {
                        "name": p.get("name"),
                        "distance_m": p.get("distance_m"),
                        "attrs": p.get("attrs"),
                        "about": (p.get("about") or "")[:180],
                    }
                    for p in s.places[:3]
                ],
                "products": [
                    {
                        "name": p.get("name"),
                        "price": p.get("price"),
                        "distance_m": p.get("distance_m"),
                        "description": (p.get("description") or "")[:180],
                        "place": (p.get("place") or {}).get("name")
                        if isinstance(p.get("place"), dict)
                        else None,
                    }
                    for p in s.products[:3]
                ],
            }
            payload.append(step)
        try:
            data = await self.deepseek.chat_json(
                phase="compose",
                system=prompts.COMPOSE_SYSTEM,
                user=prompts.compose_user_payload(q=q, steps_payload=payload),
                max_tokens=min(2048, self.deepseek.max_tokens),
            )
            msg = data.get("message") or data.get("answer")
            if isinstance(msg, str) and msg.strip():
                return msg.strip()
        except Exception as e:
            self._log("compose_fail", error=str(e))
        return self._template_message(q, steps)

    @staticmethod
    def _template_message(q: str, steps: List[MilanaSearchStepResult]) -> str:
        lines = [
            "Привет! Я Милана. Вот что нашлось под твои пожелания:",
            "",
        ]
        for i, s in enumerate(steps, 1):
            why = f" — {s.why}" if s.why else ""
            lines.append(f"{i}. {s.intent}{why} (найдено: {s.total})")
            rows = s.products if s.domain == "product" else s.places
            if not rows:
                lines.append("   Пока пусто с такими фильтрами.")
                continue
            for row in rows[:3]:
                dist = row.get("distance_m")
                dist_s = f", ~{int(dist)} м" if isinstance(dist, (int, float)) else ""
                extra = ""
                if s.domain == "product" and row.get("price") is not None:
                    extra = f" — {row.get('price')} ₽"
                    place = row.get("place")
                    if isinstance(place, dict) and place.get("name"):
                        extra += f" ({place['name']})"
                lines.append(f"   • {row.get('name')}{extra}{dist_s}")
            lines.append("")
        lines.append("Удачи и приятного вечера — если что, просто уточни запрос!")
        return "\n".join(lines).strip()
