"""Сжатие JSON Schema attrs для LLM (без description)."""

from __future__ import annotations

from typing import Any, Dict


def compact_json_schema(schema: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Убирает description и прочий шум; оставляет type/enum/min/max/items.
    Экономит токены при передаче схемы в LLM.
    """
    if not schema or not isinstance(schema, dict):
        return {"type": "object", "properties": {}}
    props_in = schema.get("properties") or {}
    props_out: Dict[str, Any] = {}
    for key, raw in props_in.items():
        if not isinstance(raw, dict):
            continue
        props_out[key] = _compact_prop(raw)
    out: Dict[str, Any] = {"type": "object", "properties": props_out}
    if "required" in schema and isinstance(schema["required"], list):
        out["required"] = list(schema["required"])
    return out


def _compact_prop(raw: Dict[str, Any]) -> Dict[str, Any]:
    item: Dict[str, Any] = {}
    if "type" in raw:
        item["type"] = raw["type"]
    if "enum" in raw:
        item["enum"] = raw["enum"]
    if "minimum" in raw:
        item["minimum"] = raw["minimum"]
    if "maximum" in raw:
        item["maximum"] = raw["maximum"]
    if "minItems" in raw:
        item["minItems"] = raw["minItems"]
    if "maxItems" in raw:
        item["maxItems"] = raw["maxItems"]
    items = raw.get("items")
    if isinstance(items, dict):
        nested: Dict[str, Any] = {}
        if "type" in items:
            nested["type"] = items["type"]
        if "enum" in items:
            nested["enum"] = items["enum"]
        if nested:
            item["items"] = nested
    return item
