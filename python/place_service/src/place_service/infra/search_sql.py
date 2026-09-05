"""SQL-хелперы для списков id в search WHERE."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

MAX_EXCLUDE_IDS = 200


def unique_positive_ids(ids: Optional[Iterable[int]], *, limit: int = MAX_EXCLUDE_IDS) -> List[int]:
    out: List[int] = []
    seen: set[int] = set()
    if not ids:
        return out
    for raw in ids:
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


def sql_not_in(
    column: str,
    ids: Optional[Iterable[int]],
    params: Dict[str, Any],
    *,
    prefix: str,
) -> Optional[str]:
    cleaned = unique_positive_ids(ids)
    if not cleaned:
        return None
    keys: List[str] = []
    for i, n in enumerate(cleaned):
        key = f"{prefix}_{i}"
        params[key] = n
        keys.append(f":{key}")
    return f"{column} NOT IN ({', '.join(keys)})"
