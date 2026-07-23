"""Агент вариант B: PLAN → compact schemas → BUILD → places/search → MESSAGE."""

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
from python.place_service.src.place_service.entities.search import PlaceSearchRequest


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
        return {"cities": cities, "categories": categories}

    async def run(self, req: MilanaPlacesSearchRequest) -> MilanaPlacesSearchResponse:
        if not self.deepseek.configured:
            raise CoreException(
                message="DEEPSEEK_API_KEY не задан — Milana не может планировать поиск без LLM",
            )

        city_id = req.city_id if req.city_id is not None else self.default_city_id
        per_step = req.limit_per_step or self.places_per_step
        my_geo = req.my_geo.model_dump() if req.my_geo else None
        weekday = req.weekday if req.weekday is not None else datetime.now().weekday()

        self._log(
            "milana_run_start",
            q=req.q,
            city_id=city_id,
            my_geo=my_geo,
            weekday=weekday,
            limit_per_step=per_step,
        )

        # --- справочники мира ---
        cities = await self.places.list_cities_compact()
        categories = await self.places.list_categories_compact()
        known_codes = {c["code"] for c in categories if c.get("code")}
        self._log(
            "world_loaded",
            cities_n=len(cities),
            categories_n=len(categories),
        )

        # --- pass 1: PLAN ---
        plan_raw = await self.deepseek.chat_json(
            phase="plan",
            system=prompts.PLAN_SYSTEM,
            user=prompts.plan_user_payload(
                q=req.q,
                cities=cities,
                categories=categories,
                city_id=city_id,
                my_geo=my_geo,
                weekday=weekday,
            ),
            max_tokens=min(2048, self.deepseek.max_tokens),
        )
        plan_steps = self._parse_plan(plan_raw, known_codes=known_codes)[: self.max_steps]
        if not plan_steps:
            raise CoreException(message="Милана не смогла построить план поиска по запросу")
        self._log("plan_ready", plan=plan_steps)

        # --- схемы только для выбранных категорий ---
        codes = [s["category"] for s in plan_steps]
        schemas = await self.places.get_attr_schemas_compact(codes)
        self._log("schemas_loaded", categories=list(schemas.keys()))

        # --- pass 2: BUILD search bodies ---
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
            ),
            max_tokens=min(4096, self.deepseek.max_tokens),
        )
        built = self._parse_build(build_raw, plan_steps=plan_steps)[: self.max_steps]
        if not built:
            raise CoreException(message="Милана не смогла собрать тела places/search")
        self._log("build_ready", steps=[{"intent": b["intent"], "search": b["search"]} for b in built])

        # --- execute searches ---
        step_results: List[MilanaSearchStepResult] = []
        for item in built:
            search_body = self._normalize_search(
                item["search"], city_id=city_id, my_geo=my_geo, limit=per_step
            )
            try:
                PlaceSearchRequest.model_validate(search_body)
            except Exception as e:
                self._log("search_validation_fail", intent=item["intent"], error=str(e), body=search_body)
                continue
            try:
                raw = await self.places.search(search_body)
            except Exception as e:
                self._log("search_exec_fail", intent=item["intent"], error=str(e))
                step_results.append(
                    MilanaSearchStepResult(
                        intent=item["intent"],
                        why=item.get("why") or "",
                        search=search_body,
                        total=0,
                        places=[],
                    )
                )
                continue
            items = raw.get("items") or []
            total = int(raw.get("total") or len(items))
            step_results.append(
                MilanaSearchStepResult(
                    intent=item["intent"],
                    why=item.get("why") or "",
                    search=search_body,
                    total=total,
                    places=self.places.slim_places(items, per_step),
                )
            )

        if not step_results:
            raise CoreException(message="Все шаги поиска отклонены валидацией")

        # --- pass 3: MESSAGE ---
        message = await self._compose_message(req.q, step_results)
        self._log("milana_run_done", steps_n=len(step_results), message_preview=message[:500])

        return MilanaPlacesSearchResponse(
            message=message,
            steps=step_results,
            plan=[MilanaPlanStep(**s) for s in plan_steps],
            model=self.deepseek.model,
            used_llm=True,
        )

    def _parse_plan(self, data: Dict[str, Any], *, known_codes: set) -> List[Dict[str, Any]]:
        steps_raw = data.get("steps")
        if not isinstance(steps_raw, list):
            raise CoreException(message="План LLM: нет массива steps")
        out: List[Dict[str, Any]] = []
        for s in steps_raw:
            if not isinstance(s, dict):
                continue
            cat = str(s.get("category") or "").strip()
            if not cat or (known_codes and cat not in known_codes):
                self._log("plan_skip_unknown_category", step=s)
                continue
            out.append(
                {
                    "intent": str(s.get("intent") or cat).strip(),
                    "category": cat,
                    "why": str(s.get("why") or "").strip(),
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
        # fallback why/intent из plan по индексу
        out: List[Dict[str, Any]] = []
        for i, s in enumerate(steps_raw):
            if not isinstance(s, dict):
                continue
            search = s.get("search")
            if not isinstance(search, dict):
                continue
            plan = plan_steps[i] if i < len(plan_steps) else {}
            out.append(
                {
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
    ) -> Dict[str, Any]:
        b = dict(body)
        b.setdefault("city_id", city_id)
        b.setdefault("limit", limit)
        b.setdefault("page", 1)
        if my_geo and not b.get("my_geo"):
            b["my_geo"] = my_geo
        if b.get("sort_by") == "distance" and not b.get("my_geo") and my_geo:
            b["my_geo"] = my_geo
        if b.get("sort_by") == "distance" and not b.get("my_geo"):
            b.pop("sort_by", None)
        return b

    async def _compose_message(self, q: str, steps: List[MilanaSearchStepResult]) -> str:
        payload = [
            {
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
            }
            for s in steps
        ]
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
            if not s.places:
                lines.append("   Пока пусто с такими фильтрами.")
                continue
            for p in s.places[:3]:
                dist = p.get("distance_m")
                dist_s = f", ~{int(dist)} м" if isinstance(dist, (int, float)) else ""
                lines.append(f"   • {p.get('name')}{dist_s}")
            lines.append("")
        lines.append("Удачи и приятного вечера — если что, просто уточни запрос!")
        return "\n".join(lines).strip()
