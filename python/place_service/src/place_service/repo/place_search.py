"""Многокритериальный поиск мест (SQL)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from sqlalchemy import select, text
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import Place
from python.place_service.src.place_service.entities.search import PlaceSearchRequest
from python.place_service.src.place_service.infra.attr_ops import compile_attrs_filters
from python.place_service.src.place_service.infra.orm.mappers import place_model_to_dto
from python.place_service.src.place_service.infra.orm.models import PlaceModel
from python.place_service.src.place_service.infra.schedule_filter import compile_open_at_filters


@dataclass
class PlaceSearchResult:
    items: List[Place]
    total: int
    page: int
    limit: int
    distances_m: Dict[int, float]  # place_id -> meters (если считали)


class PlaceSearchRepo(Protocol):
    async def search(self, req: PlaceSearchRequest) -> PlaceSearchResult: ...


@bean
class PlaceSearchRepoImpl(PlaceSearchRepo):
    db: Database

    async def search(self, req: PlaceSearchRequest) -> PlaceSearchResult:
        where = ["deleted = FALSE", "city_id = :city_id", "category_code = :category"]
        params: Dict[str, Any] = {
            "city_id": req.city_id,
            "category": req.category,
            "limit": req.limit,
            "offset": (req.page - 1) * req.limit,
        }

        if req.name:
            where.append("name ILIKE :name_pat")
            params["name_pat"] = f"%{req.name}%"

        if req.attrs:
            attrs_sql, attrs_params = compile_attrs_filters(req.attrs)
            where.append(attrs_sql)
            params.update(attrs_params)

        if req.open_at:
            oa_sql, oa_params = compile_open_at_filters(req.open_at)
            where.append(oa_sql)
            params.update(oa_params)

        where_sql = " AND ".join(where)

        distance_select = "NULL::float AS distance_m"
        order_sql = "id DESC"
        if req.sort_by == "rating":
            order_sql = "(rating_up - rating_down) DESC, rating_up DESC, id DESC"
        elif req.sort_by == "distance" and req.my_geo is not None:
            params["my_lat"] = req.my_geo.lat
            params["my_lng"] = req.my_geo.lng
            distance_select = (
                "earth_distance(ll_to_earth(lat, lng), ll_to_earth(:my_lat, :my_lng)) AS distance_m"
            )
            order_sql = "distance_m ASC NULLS LAST, id DESC"
        elif req.my_geo is not None:
            # расстояние в ответе без сортировки по нему
            params["my_lat"] = req.my_geo.lat
            params["my_lng"] = req.my_geo.lng
            distance_select = (
                "earth_distance(ll_to_earth(lat, lng), ll_to_earth(:my_lat, :my_lng)) AS distance_m"
            )

        count_sql = text(f"SELECT count(*) FROM places WHERE {where_sql}")
        list_sql = text(
            f"""
            SELECT id, {distance_select}
            FROM places
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT :limit OFFSET :offset
            """
        )

        async with self.db.session() as session:
            total = int((await session.execute(count_sql, params)).scalar_one())
            rows = (await session.execute(list_sql, params)).mappings().all()
            ids = [int(r["id"]) for r in rows]
            distances = {
                int(r["id"]): float(r["distance_m"])
                for r in rows
                if r["distance_m"] is not None
            }
            if not ids:
                return PlaceSearchResult(items=[], total=total, page=req.page, limit=req.limit, distances_m={})

            result = await session.execute(select(PlaceModel).where(PlaceModel.id.in_(ids)))
            by_id = {m.id: m for m in result.scalars().all()}
            places = [place_model_to_dto(by_id[pid]) for pid in ids if pid in by_id]

            return PlaceSearchResult(
                items=places,
                total=total,
                page=req.page,
                limit=req.limit,
                distances_m=distances,
            )
