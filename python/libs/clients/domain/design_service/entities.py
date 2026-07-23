"""DTO design-service."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class MapPinStyleOut(BaseModel):
    id: int
    code: str
    name: str
    image_url: str
    gif_url: Optional[str] = None
    anchor_x: float = 0.5
    anchor_y: float = 1.0


class ChatThemeOut(BaseModel):
    id: int
    code: str
    name: str
    background_url: str
    font_family: str = "system"
    colors: Dict[str, Any] = {}
