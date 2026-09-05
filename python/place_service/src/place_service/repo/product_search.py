"""Многокритериальный поиск продуктов (SQL, join places)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from sqlalchemy import select, text
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.libs.entities.place import Product
from python.place_service.src.place_service.entities.search import ProductSearchRequest
from python.place_service.src.place_service.infra.orm.mappers import product_model_to_dto
from python.place_service.src.place_service.infra.orm.models import ProductModel
from python.place_service.src.place_service.infra.schedule_filter import (
    compile_date_range_filters,
    compile_include_past_filter,
    compile_open_at_filters,
    event_start_expr,
)
from python.place_service.src.place_service.infra.search_sql import sql_not_in


@dataclass
class ProductSearchResult:
    items: List[Product]
    total: int
    page: int
    limit: int
    distances_m: Dict[int, float]


class ProductSearchRepo(Protocol):
    async def search(self, req: ProductSearchRequest) -> ProductSearchResult: ...


@bean
class ProductSearchRepoImpl(ProductSearchRepo):
    db: Database

    async def search(self, req: ProductSearchRequest) -> ProductSearchResult:
        where = [
            "p.deleted = FALSE",
            "pl.deleted = FALSE",
            "pl.city_id = :city_id",
        ]
        params: Dict[str, Any] = {
            "city_id": req.city_id,
            "limit": req.limit,
            "offset": (req.page - 1) * req.limit,
        }

        if req.category:
            where.append("p.category_code = :category")
            params["category"] = req.category

        if req.q:
            where.append(
                "(p.name ILIKE :q_pat OR p.description ILIKE :q_pat OR pl.name ILIKE :q_pat)"
            )
            params["q_pat"] = f"%{req.q}%"

        if req.place_id is not None:
            where.append("p.place_id = :place_id")
            params["place_id"] = req.place_id

        if req.place_name:
            where.append("pl.name ILIKE :place_name_pat")
            params["place_name_pat"] = f"%{req.place_name}%"

        if req.place_category:
            where.append("pl.category_code = :place_category")
            params["place_category"] = req.place_category

        excl = sql_not_in("p.id", req.exclude_ids, params, prefix="exid")
        if excl:
            where.append(excl)
        excl_pl = sql_not_in("p.place_id", req.exclude_place_ids, params, prefix="expl")
        if excl_pl:
            where.append(excl_pl)

        if req.price_from is not None:
            where.append("p.price IS NOT NULL AND p.price >= :price_from")
            params["price_from"] = req.price_from

        if req.price_to is not None:
            where.append("p.price IS NOT NULL AND p.price <= :price_to")
            params["price_to"] = req.price_to

        if req.open_at:
            oa_sql, oa_params = compile_open_at_filters(
                req.open_at,
                include_exceptions=True,
                include_events=True,
                schedule_column="p.schedule",
                timezone=req.timezone,
            )
            where.append(oa_sql)
            params.update(oa_params)

        date_sql, date_params = compile_date_range_filters(
            date_from=req.date_from,
            date_to=req.date_to,
            schedule_column="p.schedule",
        )
        if date_sql != "TRUE":
            where.append(date_sql)
            params.update(date_params)

        past_sql, past_params = compile_include_past_filter(
            include_past=req.include_past,
            timezone=req.timezone,
            schedule_column="p.schedule",
        )
        if past_sql != "TRUE":
            where.append(past_sql)
            params.update(past_params)

        where_sql = " AND ".join(where)
        from_sql = "products p JOIN places pl ON pl.id = p.place_id"

        distance_select = "NULL::float AS distance_m"
        event_select = "NULL::timestamp AS event_start"
        if req.my_geo is not None:
            params["my_lat"] = req.my_geo.lat
            params["my_lng"] = req.my_geo.lng
            distance_select = (
                "earth_distance(ll_to_earth(pl.lat, pl.lng), "
                "ll_to_earth(:my_lat, :my_lng)) AS distance_m"
            )
        if req.sort_by == "event_start":
            event_select = f"{event_start_expr('p.schedule')} AS event_start"

        if req.sort_by == "price":
            order_sql = "price ASC NULLS LAST, id DESC"
        elif req.sort_by == "created_at":
            order_sql = "created_at DESC, id DESC"
        elif req.sort_by == "event_start":
            order_sql = "event_start ASC NULLS LAST, id DESC"
        elif req.sort_by == "distance" and req.my_geo is not None:
            order_sql = "distance_m ASC NULLS LAST, id DESC"
        else:
            order_sql = "id DESC"

        filtered = f"""
            SELECT p.id, p.place_id, p.price, p.created_at,
                   {distance_select}, {event_select}
            FROM {from_sql}
            WHERE {where_sql}
        """

        if req.one_per_place:
            ranked = f"""
                SELECT * FROM (
                    SELECT f.*,
                           ROW_NUMBER() OVER (
                               PARTITION BY f.place_id ORDER BY {order_sql}
                           ) AS rn
                    FROM ({filtered}) f
                ) ranked
                WHERE rn = 1
            """
            count_sql = text(
                f"SELECT count(*) FROM (SELECT DISTINCT p.place_id FROM {from_sql} WHERE {where_sql}) t"
            )
            list_sql = text(
                f"""
                SELECT id, distance_m FROM ({ranked}) x
                ORDER BY {order_sql}
                LIMIT :limit OFFSET :offset
                """
            )
        else:
            count_sql = text(f"SELECT count(*) FROM {from_sql} WHERE {where_sql}")
            list_sql = text(
                f"""
                SELECT id, distance_m FROM ({filtered}) f
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
                return ProductSearchResult(
                    items=[],
                    total=total,
                    page=req.page,
                    limit=req.limit,
                    distances_m={},
                )

            result = await session.execute(select(ProductModel).where(ProductModel.id.in_(ids)))
            by_id = {m.id: m for m in result.scalars().all()}
            products = [product_model_to_dto(by_id[pid]) for pid in ids if pid in by_id]
            return ProductSearchResult(
                items=products,
                total=total,
                page=req.page,
                limit=req.limit,
                distances_m=distances,
            )
