"""Модели запроса/ответа milana places NL search."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MilanaGeo(BaseModel):
    lat: float
    lng: float


class MilanaPlacesSearchRequest(BaseModel):
    """NL-запрос пользователя → агент строит и вызывает places/search."""

    q: str = Field(..., min_length=2, description="Произвольный текст пожеланий на русском")
    city_id: Optional[int] = Field(
        None,
        description="ID города (если не указан — milana.default_city_id из config)",
    )
    my_geo: Optional[MilanaGeo] = Field(
        None,
        description="Гео пользователя (для distance и «недалеко»)",
    )
    weekday: Optional[int] = Field(
        None,
        ge=0,
        le=6,
        description="День недели 0=пн…6=вс, если в тексте день не указан явно",
    )
    limit_per_step: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Сколько мест на шаг маршрута (default из config)",
    )

    @field_validator("q")
    @classmethod
    def _q_strip(cls, v: str) -> str:
        s = (v or "").strip()
        if len(s) < 2:
            raise ValueError("q слишком короткий")
        return s


class MilanaPlanStep(BaseModel):
    intent: str
    category: str
    why: str = ""


class MilanaSearchStepResult(BaseModel):
    intent: str
    why: str = ""
    search: Dict[str, Any]
    total: int = 0
    places: List[Dict[str, Any]] = Field(default_factory=list)


class MilanaPlacesSearchResponse(BaseModel):
    message: str = Field(
        ...,
        description="Текст от Миланы для пользователя (приветствие + подборка + пожелание)",
    )
    steps: List[MilanaSearchStepResult] = Field(default_factory=list)
    plan: List[MilanaPlanStep] = Field(
        default_factory=list,
        description="Pass-1 план: intent/category/why",
    )
    model: Optional[str] = Field(None, description="Модель LLM")
    used_llm: bool = True
