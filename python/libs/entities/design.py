"""Дизайны пинов карты и тем чата (design-service)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from python.libs.entities.common import Entity


@dataclass
class MapPinStyle(Entity):
    """Визуальный стиль пина на карте."""

    code: str
    name: str
    image_url: str
    gif_url: Optional[str] = None
    anchor_x: float = 0.5
    anchor_y: float = 1.0


@dataclass
class ChatTheme(Entity):
    """Тема оформления чата места."""

    code: str
    name: str
    background_url: str
    font_family: str = "system"
    colors: Dict[str, Any] = field(default_factory=dict)
