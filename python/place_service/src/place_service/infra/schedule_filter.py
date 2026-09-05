"""SQL-фрагменты: open_at, events, date range, include_past."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from python.place_service.src.place_service.entities.search import SearchOpenAt

DEFAULT_TZ = "Asia/Novosibirsk"


def compile_open_at_filters(
    open_at: List[SearchOpenAt],
    *,
    include_exceptions: bool = False,
    include_events: bool = False,
    schedule_column: str = "schedule",
    timezone: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Для каждого элемента open_at (AND):
      period с weekday + interval покрывает open,
      и/или exception на этот weekday,
      и/или event, чей локальный старт в этот weekday и момент попадает в [start, end).
    """
    if not open_at:
        return ("TRUE", {})

    clauses: List[str] = []
    params: Dict[str, Any] = {}

    for i, item in enumerate(open_at):
        time_params: List[str] = []
        for j, iv in enumerate(item.intervals):
            t = _normalize_hhmm(iv.open)
            p = f"oa_{i}_{j}_t"
            params[p] = t
            time_params.append(f":{p}")

        wd = f"oa_{i}_wd"
        params[wd] = item.weekday

        time_ors = " OR ".join(
            f"place_interval_covers(iv->>'open', iv->>'close', {tp})" for tp in time_params
        )
        period_match = f"""
            EXISTS (
              SELECT 1
              FROM jsonb_array_elements(COALESCE({schedule_column}->'periods', '[]'::jsonb)) AS period
              WHERE (period->>'weekday')::int = :{wd}
                AND COALESCE((period->>'closed')::boolean, false) = false
                AND EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(period->'intervals') AS iv
                  WHERE {time_ors}
                )
            )
        """
        extra = ""
        if include_exceptions:
            extra += f"""
            OR EXISTS (
              SELECT 1
              FROM jsonb_array_elements(COALESCE({schedule_column}->'exceptions', '[]'::jsonb)) AS ex
              WHERE COALESCE((ex->>'closed')::boolean, false) = false
                AND (EXTRACT(ISODOW FROM (ex->>'date')::date)::int - 1) = :{wd}
                AND EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(COALESCE(ex->'intervals', '[]'::jsonb)) AS iv
                  WHERE {time_ors}
                )
            )
            """
        if include_events:
            instant_ors = " OR ".join(
                f"""(
                    (date_trunc('day', (ev->>'start')::timestamp)
                     + CAST({tp} AS time)) >= (ev->>'start')::timestamp
                    AND (date_trunc('day', (ev->>'start')::timestamp)
                     + CAST({tp} AS time)) < (ev->>'end')::timestamp
                )"""
                for tp in time_params
            )
            extra += f"""
            OR EXISTS (
              SELECT 1
              FROM jsonb_array_elements(COALESCE({schedule_column}->'events', '[]'::jsonb)) AS ev
              WHERE (EXTRACT(ISODOW FROM (ev->>'start')::timestamp)::int - 1) = :{wd}
                AND ({instant_ors})
            )
            """
        clauses.append(
            f"""(
            {schedule_column} IS NOT NULL
            AND ({period_match} {extra})
            )"""
        )

    return ("(" + " AND ".join(clauses) + ")", params)


def compile_date_range_filters(
    *,
    date_from: Optional[date],
    date_to: Optional[date],
    schedule_column: str = "schedule",
) -> Tuple[str, Dict[str, Any]]:
    if date_from is None and date_to is None:
        return ("TRUE", {})
    params: Dict[str, Any] = {}
    d0 = date_from or date(1970, 1, 1)
    d1 = date_to or date(2999, 12, 31)
    params["df"] = d0
    params["dt"] = d1
    sql = f"""
    (
      EXISTS (
        SELECT 1
        FROM jsonb_array_elements(COALESCE({schedule_column}->'events', '[]'::jsonb)) AS ev
        WHERE (ev->>'start')::date <= :dt
          AND (ev->>'end')::date >= :df
      )
      OR EXISTS (
        SELECT 1
        FROM jsonb_array_elements(COALESCE({schedule_column}->'exceptions', '[]'::jsonb)) AS ex
        WHERE COALESCE((ex->>'closed')::boolean, false) = false
          AND (ex->>'date')::date >= :df
          AND (ex->>'date')::date <= :dt
      )
    )
    """
    return (sql, params)


def compile_include_past_filter(
    *,
    include_past: bool,
    timezone: Optional[str],
    schedule_column: str = "schedule",
) -> Tuple[str, Dict[str, Any]]:
    if include_past:
        return ("TRUE", {})
    tz = timezone or DEFAULT_TZ
    now = datetime.now(ZoneInfo(tz))
    params = {"past_now": now, "past_tz": tz}
    sql = f"""
    (
      COALESCE(jsonb_array_length({schedule_column}->'events'), 0) = 0
      OR EXISTS (
        SELECT 1
        FROM jsonb_array_elements(COALESCE({schedule_column}->'events', '[]'::jsonb)) AS ev
        WHERE ((ev->>'end')::timestamp AT TIME ZONE COALESCE({schedule_column}->>'timezone', :past_tz))
              >= :past_now
      )
    )
    """
    return (sql, params)


def event_start_expr(schedule_column: str = "p.schedule") -> str:
    return f"""(
      SELECT MIN((ev->>'start')::timestamp)
      FROM jsonb_array_elements(COALESCE({schedule_column}->'events', '[]'::jsonb)) AS ev
    )"""


def _normalize_hhmm(value: str) -> str:
    parts = value.strip().split(":")
    if len(parts) < 2:
        raise ValueError(f"Некорректное время: {value}")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Некорректное время: {value}")
    return f"{h:02d}:{m:02d}"
