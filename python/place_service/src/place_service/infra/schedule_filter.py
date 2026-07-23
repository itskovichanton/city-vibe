"""SQL-фрагменты для проверки «открыто в момент open_at» по schedule jsonb."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from python.place_service.src.place_service.entities.search import SearchOpenAt


def compile_open_at_filters(open_at: List[SearchOpenAt]) -> Tuple[str, Dict[str, Any]]:
    """
    Для каждого элемента open_at (AND):
      существует period с weekday, closed=false,
      и interval, покрывающий время open (с учётом перехода через полночь).
    """
    if not open_at:
        return ("TRUE", {})

    clauses: List[str] = []
    params: Dict[str, Any] = {}

    for i, item in enumerate(open_at):
        # берём первый open из intervals (типичный кейс); все intervals — OR внутри дня
        time_params: List[str] = []
        for j, iv in enumerate(item.intervals):
            t = _normalize_hhmm(iv.open)
            p = f"oa_{i}_{j}_t"
            params[p] = t
            time_params.append(f":{p}")

        wd = f"oa_{i}_wd"
        params[wd] = item.weekday

        # SQL: для period weekday match AND not closed AND any interval covers any requested time
        time_ors = " OR ".join(
            f"place_interval_covers(iv->>'open', iv->>'close', {tp})" for tp in time_params
        )
        clauses.append(
            f"""(
            schedule IS NOT NULL
            AND EXISTS (
              SELECT 1
              FROM jsonb_array_elements(schedule->'periods') AS period
              WHERE (period->>'weekday')::int = :{wd}
                AND COALESCE((period->>'closed')::boolean, false) = false
                AND EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(period->'intervals') AS iv
                  WHERE {time_ors}
                )
            )
            )"""
        )

    return ("(" + " AND ".join(clauses) + ")", params)


def _normalize_hhmm(value: str) -> str:
    parts = value.strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"Некорректное время: {value}")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Некорректное время: {value}")
    return f"{h:02d}:{m:02d}"


# SQL function created in migration — fallback inline expression used if function missing.
INTERVAL_COVERS_SQL = """
CREATE OR REPLACE FUNCTION _interval_covers(open_t text, close_t text, t text)
RETURNS boolean
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    WHEN open_t IS NULL OR close_t IS NULL OR t IS NULL THEN false
    WHEN open_t <= close_t THEN (t >= open_t AND t < close_t)
    ELSE (t >= open_t OR t < close_t)  -- через полночь
  END;
$$;
"""
