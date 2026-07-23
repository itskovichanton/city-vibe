"""Расписание работы места (WeeklySchedule → jsonb)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import List, Optional


@dataclass
class TimeInterval:
    """Интервал открытости. close < open означает переход через полночь."""

    open: time
    close: time


@dataclass
class DaySchedule:
    """Расписание одного дня недели (0=пн … 6=вс)."""

    weekday: int
    closed: bool = False
    intervals: List[TimeInterval] = field(default_factory=list)


@dataclass
class ScheduleException:
    """Исключение на конкретную дату (праздник, разовое закрытие)."""

    date: date
    closed: bool = False
    intervals: Optional[List[TimeInterval]] = None
    note: Optional[str] = None


@dataclass
class WeeklySchedule:
    """Недельное расписание + исключения."""

    timezone: str = "Europe/Moscow"
    periods: List[DaySchedule] = field(default_factory=list)
    exceptions: List[ScheduleException] = field(default_factory=list)
