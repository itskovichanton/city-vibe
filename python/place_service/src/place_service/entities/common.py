"""DTO уровня API place-service."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from python.libs.entities.geo import GeoLocation
from python.place_service.src.place_service.entities.search import PlaceSearchRequest, ProductSearchRequest


@dataclass
class CityResponse:
    """Город в ответе API."""

    id: int
    name: str
    slug: str
    region: str = ""
    geo: Optional[GeoLocation] = None
    is_major: bool = True
    sort_order: int = 0
    about: str = ""
    deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Заполняется в GET /cities/nearest (метры до запрошенной точки).
    distance_m: Optional[float] = None


@dataclass
class NearestCityRequest:
    lat: float
    lng: float


@dataclass
class GetAttrSchemaRequest:
    category_code: str
    compact: bool = False


@dataclass
class CreatePlaceRequest:
    name: str
    about: str
    category: str
    owner_id: int
    lat: float
    lng: float
    attrs: dict[str, Any] = field(default_factory=dict)
    schedule: Optional[dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ListPlacesRequest:
    owner_id: Optional[int] = None
    category: Optional[str] = None
    bbox: Optional[tuple[float, float, float, float]] = None
    limit: int = 100


@dataclass
class PatchPlaceRequest:
    place_id: int
    name: Optional[str] = None
    about: Optional[str] = None
    category: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    attrs: Optional[dict[str, Any]] = None
    schedule: Optional[dict[str, Any]] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
    contacts: Optional[list[dict[str, Any]]] = None
    fields_set: frozenset[str] = field(default_factory=frozenset)


@dataclass
class DeletePlaceRequest:
    place_id: int


@dataclass
class DeletePlaceResponse:
    ok: bool
    place_id: int


# Re-export для use-case слоя (search body уже валидируется pydantic в presenter).
SearchPlacesRequest = PlaceSearchRequest
SearchProductsRequest = ProductSearchRequest


@dataclass
class CreateProductRequest:
    place_id: int
    name: str
    description: str
    category: str
    price: Optional[float] = None
    schedule: Optional[dict[str, Any]] = None


@dataclass
class ListProductsRequest:
    place_id: Optional[int] = None
    category: Optional[str] = None
    limit: int = 100


@dataclass
class PatchProductRequest:
    product_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    schedule: Optional[dict[str, Any]] = None
    fields_set: frozenset[str] = field(default_factory=frozenset)


@dataclass
class DeleteProductRequest:
    product_id: int


@dataclass
class DeleteProductResponse:
    ok: bool
    product_id: int

