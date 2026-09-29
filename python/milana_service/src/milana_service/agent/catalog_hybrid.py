"""Гибридный catalog/match: алиасы (recall) + DeepSeek по порциям (precision).

effort (УсилиеПоиска) — максимум строк справочника в одном вызове LLM.
Весь справочник проходится порциями этого размера, результаты объединяются.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.milana_service.src.milana_service.agent import prompts
from python.milana_service.src.milana_service.infra.agent_log import log_agent
from python.milana_service.src.milana_service.infra.deepseek import DeepSeekClient
from python.milana_service.src.milana_service.infra.place_search_client import PlaceSearchHttpClient
from python.place_service.src.place_service.infra.catalog_registry import resolve_catalog

_MIN_CONFIDENCE = 0.35
_MAX_EFFORT = 80


def chunk_rows(rows: Sequence[dict], effort: int) -> List[List[dict]]:
    """Нарезать справочник порциями по effort (УсилиеПоиска)."""
    size = int(effort or 0)
    if size <= 0 or not rows:
        return []
    size = min(size, _MAX_EFFORT)
    return [list(rows[i : i + size]) for i in range(0, len(rows), size)]


def parse_llm_items(raw: Any, allowed_keys: set[str]) -> List[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return []
    items = raw.get("items")
    if not isinstance(items, list):
        return []
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or item.get("code") or item.get("slug") or "").strip()
        if not key or key not in allowed_keys or key in seen:
            continue
        try:
            confidence = float(item.get("confidence") or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < _MIN_CONFIDENCE:
            continue
        why = str(item.get("why") or "").strip() or "смысловое совпадение"
        seen.add(key)
        out.append({"key": key, "why": why, "confidence": min(1.0, max(0.0, confidence))})
    return out


def merge_hits(
    rows_by_key: Dict[str, dict],
    cheap_items: Iterable[dict],
    llm_items: Iterable[dict],
    *,
    limit: int,
) -> List[dict]:
    scores: Dict[str, float] = {}
    reasons: Dict[str, str] = {}
    sources: Dict[str, str] = {}

    for item in cheap_items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("code") or item.get("slug") or "").strip()
        if not key or key not in rows_by_key:
            continue
        try:
            scores[key] = float(item.get("score") or 0)
        except (TypeError, ValueError):
            scores[key] = 1.0
        reasons[key] = str(item.get("why") or "").strip() or "алиас / поле title"
        sources[key] = "alias"

    for item in llm_items:
        key = str(item.get("key") or "").strip()
        if not key or key not in rows_by_key:
            continue
        conf = float(item.get("confidence") or 0)
        llm_score = 3.0 + 7.0 * conf
        why = str(item.get("why") or "").strip()
        if key in scores:
            scores[key] = max(scores[key], llm_score) + 1.5
            sources[key] = "both"
            if why:
                reasons[key] = why
        else:
            scores[key] = llm_score
            sources[key] = "llm"
            reasons[key] = why or "смысловое совпадение"

    ranked = sorted(scores.keys(), key=lambda k: (-scores[k], k))[: max(1, limit)]
    out: List[dict] = []
    for key in ranked:
        row = dict(rows_by_key[key])
        row["why"] = reasons[key]
        row["score"] = round(scores[key], 2)
        row["source"] = sources[key]
        out.append(row)
    return out


def _row_key(row: dict, key_field: str) -> str:
    return str(row.get(key_field) or row.get("code") or row.get("slug") or "").strip()


def _row_title(row: dict) -> str:
    return str(row.get("title") or row.get("name") or "").strip()


@bean(default_effort=("milana.catalog_match_effort", int, 50))
class CatalogHybridMatcher:
    """Алиасы place-service + порции DeepSeek (effort строк на вызов)."""

    places: PlaceSearchHttpClient
    deepseek: DeepSeekClient
    logger_service: LoggerService

    def init(self, **kwargs):
        self.default_effort = int(kwargs.get("default_effort") or 50)
        self._flog = self.logger_service.get_file_logger("milana-agent", max_line_len=0)

    def _log(self, event: str, **payload: Any) -> None:
        log_agent(self._flog, event, **payload)

    async def match(
        self,
        prompt: str,
        *,
        catalog: str | None = None,
        entity_type: str | None = None,
        fields: List[str] | None = None,
        limit: int = 8,
        effort: int | None = None,
    ) -> Dict[str, Any]:
        spec = resolve_catalog(catalog, entity_type)
        effort_n = self.default_effort if effort is None else int(effort)
        effort_n = max(0, min(effort_n, _MAX_EFFORT))
        limit_n = max(1, min(int(limit or 8), 50))

        rows = await self._load_rows(spec.code)
        rows_by_key = {}
        for row in rows:
            key = _row_key(row, spec.key_field)
            if key:
                rows_by_key[key] = row

        cheap: Dict[str, Any] = {}
        try:
            cheap = await self.places.match_catalog(
                prompt,
                spec.code,
                fields=fields,
                limit=min(50, max(limit_n, 16)),
            )
        except Exception as e:
            self._log("catalog_cheap_fail", catalog=spec.code, error=str(e))
        cheap_items = cheap.get("items") if isinstance(cheap, dict) else []
        if not isinstance(cheap_items, list):
            cheap_items = []

        llm_items: List[Dict[str, Any]] = []
        used_llm = False
        if effort_n > 0 and self.deepseek.configured and rows:
            used_llm = True
            llm_items = await self._llm_scan(prompt, spec.code, spec.key_field, rows, effort_n)
        elif effort_n > 0 and not self.deepseek.configured:
            self._log("catalog_llm_skip", reason="DEEPSEEK_API_KEY не задан")

        items = merge_hits(rows_by_key, cheap_items, llm_items, limit=limit_n)
        self._log(
            "catalog_hybrid_done",
            catalog=spec.code,
            effort=effort_n,
            used_llm=used_llm,
            cheap_n=len(cheap_items),
            llm_n=len(llm_items),
            out_n=len(items),
        )
        return {
            "catalog": spec.code,
            "entity_type": spec.entity_type,
            "prompt": (prompt or "").strip(),
            "fields": list(fields or spec.text_fields),
            "effort": effort_n,
            "used_llm": used_llm,
            "items": items,
        }

    async def _load_rows(self, catalog: str) -> List[dict]:
        if catalog == "product_categories":
            return await self.places.list_product_categories_compact()
        if catalog == "place_categories":
            return await self.places.list_categories_compact()
        if catalog == "cities":
            return await self.places.list_cities_compact()
        raise CoreException(message=f"Справочник {catalog} не загружается")

    async def _llm_scan(
        self,
        prompt: str,
        catalog: str,
        key_field: str,
        rows: List[dict],
        effort: int,
    ) -> List[Dict[str, Any]]:
        batches = chunk_rows(rows, effort)
        found: List[Dict[str, Any]] = []
        for i, batch in enumerate(batches, 1):
            payload_rows = []
            allowed: set[str] = set()
            for row in batch:
                key = _row_key(row, key_field)
                if not key:
                    continue
                allowed.add(key)
                payload_rows.append({"key": key, "title": _row_title(row)})
            if not payload_rows:
                continue
            try:
                raw = await self.deepseek.chat_json(
                    phase=f"catalog_match:{catalog}:{i}/{len(batches)}",
                    system=prompts.CATALOG_MATCH_SYSTEM,
                    user=prompts.catalog_match_user_payload(prompt=prompt, rows=payload_rows),
                    max_tokens=min(1024, self.deepseek.max_tokens),
                )
            except Exception as e:
                self._log(
                    "catalog_llm_batch_fail",
                    catalog=catalog,
                    batch=i,
                    batches=len(batches),
                    error=str(e),
                )
                continue
            found.extend(parse_llm_items(raw, allowed))
        return found
