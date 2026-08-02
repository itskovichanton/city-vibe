"""Pydantic-модели HTTP-запросов (presenter)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GeoIn(BaseModel):
    latitude: float
    longitude: float


class PlaceCreateBody(BaseModel):
    name: str
    about: str
    category: str = Field(..., description="Код категории (PlaceCategory)")
    owner_id: int
    geo: GeoIn
    attrs: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: List[Dict[str, Any]] = Field(default_factory=list)


class PlacePatchBody(BaseModel):
    name: Optional[str] = None
    about: Optional[str] = None
    category: Optional[str] = None
    geo: Optional[GeoIn] = None
    attrs: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: Optional[List[Dict[str, Any]]] = None
