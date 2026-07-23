#!/usr/bin/env python3
"""
Seed: все категории + уникальные JSON Schema + 10_000 мест в Новосибирске.

Usage (из корня репо):
  PYTHONPATH=. python python/place_service/scripts/seed_nsk_places.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "python" / "place_service" / "src"))

import asyncpg  # noqa: E402

from python.libs.entities.place import (  # noqa: E402
    PLACE_CATEGORY_TITLES,
    PLACE_CATEGORY_TITLES_EN,
    PlaceCategory,
)
from python.place_service.src.place_service.infra.category_schemas import schema_for  # noqa: E402

DSN = "postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_places"
PLACES_COUNT = 10_000
BATCH = 500
OWNER_ID = 1
NSK_SLUG = "novosibirsk"

# Примерный bbox Новосибирска
LAT_MIN, LAT_MAX = 54.86, 55.12
LNG_MIN, LNG_MAX = 82.78, 83.12

NAME_PREFIXES = [
    "Сибирский", "Обской", "Академический", "Центральный", "Левобережный",
    "Правый", "Золотой", "Северный", "Южный", "Тихий", "Яркий", "Новый",
    "Старый", "Горный", "Речной", "Городской", "Домашний", "Уютный",
]
NAME_SUFFIXES = [
    "угол", "двор", "свет", "ритм", "вкус", "дом", "клуб", "мир", "порт",
    "сад", "остров", "маяк", "мост", "квартал", "лофт", "хаб", "точка",
]
ABOUT_TEMPLATES = [
    "Популярное место среди жителей Новосибирска. {extra}",
    "Уютная атмосфера и внимательный персонал. {extra}",
    "Идеально для встреч с друзьями после работы. {extra}",
    "Локация с характером — загляните сами. {extra}",
    "Семейный формат и понятные цены. {extra}",
]
EXTRAS = [
    "Рядом остановка общественного транспорта.",
    "Есть парковка у входа.",
    "Часто проходят тематические вечера.",
    "Любимчики местных блогеров.",
    "Открыты допоздна по выходным.",
    "Летом особенно приятно на веранде.",
]


def _rand_attrs(category: PlaceCategory, rng: random.Random) -> dict:
    schema = schema_for(category)
    props = schema.get("properties") or {}
    attrs: dict = {}
    # 30–80% свойств заполняем, все optional
    keys = list(props.keys())
    rng.shuffle(keys)
    n = rng.randint(max(1, len(keys) // 3), max(1, (len(keys) * 4) // 5)) if keys else 0
    for key in keys[:n]:
        spec = props[key]
        attrs[key] = _sample_value(spec, rng)
    return attrs


def _sample_value(spec: dict, rng: random.Random):
    t = spec.get("type")
    if t == "boolean":
        return rng.choice([True, False])
    if t == "integer":
        if "enum" in spec:
            return rng.choice(spec["enum"])
        lo = spec.get("minimum", 0)
        hi = spec.get("maximum", 100)
        return rng.randint(int(lo), int(hi))
    if t == "number":
        lo = float(spec.get("minimum", 0))
        hi = float(spec.get("maximum", 100))
        return round(rng.uniform(lo, hi), 2)
    if t == "string":
        if "enum" in spec:
            return rng.choice(spec["enum"])
        return rng.choice(["nice", "local", "cozy", "popular"])
    if t == "array":
        item = spec.get("items") or {}
        if item.get("enum"):
            pool = list(item["enum"])
            k = rng.randint(1, min(3, len(pool)))
            return rng.sample(pool, k)
        return []
    return None


def _schedule(rng: random.Random) -> dict | None:
    if rng.random() < 0.25:
        return None
    open_h = rng.choice([8, 9, 10, 11, 12, 14, 16, 18])
    close_h = rng.choice([20, 21, 22, 23, 0, 1, 2])
    periods = []
    for wd in range(7):
        closed = wd == 0 and rng.random() < 0.15
        periods.append(
            {
                "weekday": wd,
                "closed": closed,
                "intervals": []
                if closed
                else [{"open": f"{open_h:02d}:00", "close": f"{close_h:02d}:00"}],
            }
        )
    return {"timezone": "Asia/Novosibirsk", "periods": periods, "exceptions": []}


def _contacts(idx: int, rng: random.Random) -> list[dict]:
    """1–3 контакта: телефон Новосибирска (+7383…) и/или email."""
    contacts: list[dict] = []
    cid = 1
    # всегда телефон
    phone = f"+7383{rng.randint(2000000, 3999999)}"
    contacts.append(
        {
            "id": cid,
            "type": "phone",
            "value": phone,
            "verified": rng.random() < 0.7,
            "deleted": False,
        }
    )
    cid += 1
    if rng.random() < 0.75:
        slug = f"place{idx}"
        domain = rng.choice(["nsk.ru", "sibmail.ru", "cityvibe.local", "yandex.ru", "mail.ru"])
        contacts.append(
            {
                "id": cid,
                "type": "email",
                "value": f"info@{slug}.{domain}" if domain == "cityvibe.local" else f"{slug}@{domain}",
                "verified": rng.random() < 0.4,
                "deleted": False,
            }
        )
        cid += 1
    if rng.random() < 0.25:
        # второй телефон (мобильный)
        mobile = f"+7900{rng.randint(1000000, 9999999)}"
        contacts.append(
            {
                "id": cid,
                "type": "phone",
                "value": mobile,
                "verified": rng.random() < 0.5,
                "deleted": False,
            }
        )
    return contacts


def _name(category: PlaceCategory, idx: int, rng: random.Random) -> str:
    title = PLACE_CATEGORY_TITLES[category]
    style = rng.randint(0, 3)
    if style == 0:
        return f"{rng.choice(NAME_PREFIXES)} {title[:-1] if title.endswith('ы') else title} #{idx}"
    if style == 1:
        return f"{rng.choice(NAME_PREFIXES)} {rng.choice(NAME_SUFFIXES)}"
    if style == 2:
        return f"{title}: {rng.choice(NAME_SUFFIXES).title()} {idx}"
    return f"«{rng.choice(NAME_PREFIXES)} {rng.choice(NAME_SUFFIXES)}»"


async def main() -> None:
    rng = random.Random(42)
    categories = list(PlaceCategory)
    print(f"Categories: {len(categories)}")

    conn = await asyncpg.connect(DSN)
    try:
        city_id = await conn.fetchval(
            "SELECT id FROM cities WHERE slug = $1 AND deleted = FALSE", NSK_SLUG
        )
        if city_id is None:
            raise SystemExit(f"City {NSK_SLUG} not found — run seed-place cities first")
        print(f"Novosibirsk city_id={city_id}")

        # categories upsert
        for i, cat in enumerate(categories):
            await conn.execute(
                """
                INSERT INTO place_categories (code, title, title_en, sort_order, is_active, deleted)
                VALUES ($1, $2, $3, $4, TRUE, FALSE)
                ON CONFLICT (code) DO UPDATE SET
                    title = EXCLUDED.title,
                    title_en = EXCLUDED.title_en,
                    sort_order = EXCLUDED.sort_order,
                    is_active = TRUE,
                    deleted = FALSE,
                    updated_at = NOW()
                """,
                cat.value,
                PLACE_CATEGORY_TITLES[cat],
                PLACE_CATEGORY_TITLES_EN.get(cat, cat.value),
                (i + 1) * 10,
            )
        print("place_categories upserted")

        # schemas upsert (always refresh)
        for cat in categories:
            schema = schema_for(cat)
            await conn.execute(
                """
                INSERT INTO attr_schemas (category_code, version, json_schema, deleted)
                VALUES ($1, 2, $2::jsonb, FALSE)
                ON CONFLICT (category_code) DO UPDATE SET
                    version = EXCLUDED.version,
                    json_schema = EXCLUDED.json_schema,
                    deleted = FALSE,
                    updated_at = NOW()
                """,
                cat.value,
                json.dumps(schema, ensure_ascii=False),
            )
        print("attr_schemas upserted")

        # replace NSK seed places
        status = await conn.execute("DELETE FROM places WHERE city_id = $1", city_id)
        print(f"cleared old NSK places: {status}")

        # generate places
        rows = []
        for i in range(1, PLACES_COUNT + 1):
            cat = categories[i % len(categories)]
            # weight popular food/entertainment a bit more via second pick sometimes
            if rng.random() < 0.35:
                cat = rng.choice(
                    [
                        PlaceCategory.RESTAURANTS,
                        PlaceCategory.CAFES,
                        PlaceCategory.BARS,
                        PlaceCategory.GYMS,
                        PlaceCategory.QUESTS,
                        PlaceCategory.SUSHI,
                        PlaceCategory.PIZZA,
                        PlaceCategory.COFFEE_ROASTERS,
                        PlaceCategory.PARKS,
                        PlaceCategory.CINEMA,
                    ]
                )
            lat = round(rng.uniform(LAT_MIN, LAT_MAX), 6)
            lng = round(rng.uniform(LNG_MIN, LNG_MAX), 6)
            attrs = _rand_attrs(cat, rng)
            schedule = _schedule(rng)
            about = rng.choice(ABOUT_TEMPLATES).format(extra=rng.choice(EXTRAS))
            rows.append(
                (
                    _name(cat, i, rng),
                    about,
                    cat.value,
                    OWNER_ID,
                    city_id,
                    lat,
                    lng,
                    json.dumps(attrs, ensure_ascii=False),
                    json.dumps(schedule, ensure_ascii=False) if schedule else None,
                    None,  # pin_style_id default later
                    None,  # chat_theme_id
                    rng.randint(0, 80),
                    rng.randint(0, 20),
                    json.dumps(_contacts(i, rng), ensure_ascii=False),
                )
            )
            if len(rows) >= BATCH:
                await _insert_batch(conn, rows)
                print(f"  inserted {i}/{PLACES_COUNT}")
                rows.clear()
        if rows:
            await _insert_batch(conn, rows)

        total = await conn.fetchval(
            "SELECT count(*) FROM places WHERE city_id = $1 AND deleted = FALSE", city_id
        )
        cats = await conn.fetchval("SELECT count(*) FROM place_categories WHERE deleted = FALSE")
        schemas = await conn.fetchval("SELECT count(*) FROM attr_schemas WHERE deleted = FALSE")
        dist = await conn.fetch(
            """
            SELECT category_code, count(*) AS n
            FROM places WHERE city_id = $1 AND deleted = FALSE
            GROUP BY category_code ORDER BY n DESC LIMIT 15
            """,
            city_id,
        )
        print(f"OK places={total} categories={cats} schemas={schemas}")
        print("top categories:")
        for r in dist:
            print(f"  {r['category_code']}: {r['n']}")
    finally:
        await conn.close()


async def _insert_batch(conn: asyncpg.Connection, rows: list) -> None:
    await conn.executemany(
        """
        INSERT INTO places (
            name, about, category_code, owner_id, city_id, lat, lng,
            attrs, schedule, pin_style_id, chat_theme_id,
            rating_up, rating_down, contacts, deleted
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7,
            $8::jsonb, $9::jsonb, $10, $11,
            $12, $13, $14::jsonb, FALSE
        )
        """,
        rows,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
