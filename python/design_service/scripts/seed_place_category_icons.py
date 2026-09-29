#!/usr/bin/env python3
"""Иконки категорий мест: assets → S3 (place_categories/{code}.png) → icon_url в БД.

Usage (из корня репо):
  PYTHONPATH=. python python/design_service/scripts/seed_place_category_icons.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

import asyncpg  # noqa: E402
import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402
from PIL import Image  # noqa: E402

ASSETS_DIR = REPO_ROOT / "python" / "design_service" / "assets" / "place_categories"
DSN = "postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_places"
S3_ENDPOINT = "http://localhost:9000"
S3_ACCESS = "minioadmin"
S3_SECRET = "minioadmin"
S3_BUCKET = "city-vibe"
KEY_PREFIX = "place_categories"
ICON_SIZE = 128

# Все коды PlaceCategory (см. python/libs/entities/place.py).
CATEGORY_CODES = [
    "bars",
    "restaurants",
    "cafes",
    "hookah",
    "concerts",
    "theaters",
    "parks",
    "exhibitions",
    "sports",
    "shopping",
    "cinema",
    "nightclubs",
    "gyms",
    "swimming_pools",
    "quests",
    "bowling",
    "karaoke",
    "billiards",
    "spa",
    "beauty_salons",
    "barbershops",
    "museums",
    "libraries",
    "coworking",
    "bakeries",
    "street_food",
    "sushi",
    "pizza",
    "burgers",
    "dessert_cafes",
    "wine_bars",
    "brewpubs",
    "lounges",
    "rooftop_bars",
    "paintball",
    "karting",
    "skating_rinks",
    "climbing",
    "yoga",
    "dance_studios",
    "jazz_clubs",
    "comedy_clubs",
    "bookstores",
    "board_game_cafes",
    "pet_cafes",
    "vr_arenas",
    "laser_tag",
    "aquaparks",
    "zoos",
    "planetariums",
    "photo_studios",
    "workshops",
    "pottery",
    "art_galleries",
    "flower_shops",
    "antique",
    "flea_markets",
    "farmers_markets",
    "music_schools",
    "escape_rooms",
    "mini_golf",
    "saunas",
    "banya",
    "hookah_lounges",
    "teahouses",
    "coffee_roasters",
    "food_trucks",
    "markets",
    "malls",
    "waterfronts",
    "viewpoints",
    "children_centers",
    "playgrounds",
]


def to_mask_png(src: Path, dest: Path, size: int = ICON_SIZE) -> None:
    """Белые штрихи на чёрном → белый RGB + альфа, кроп по глифу, 128×128."""
    im = Image.open(src).convert("RGB")
    gray = im.convert("L")
    alpha = gray.point(lambda p: 0 if p < 16 else p)
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"пустая иконка: {src}")
    cropped_a = alpha.crop(bbox)
    gw, gh = cropped_a.size
    target = int(size * 0.72)
    scale = target / max(gw, gh)
    nw = max(1, round(gw * scale))
    nh = max(1, round(gh * scale))
    cropped_a = cropped_a.resize((nw, nh), Image.Resampling.LANCZOS)
    white = Image.new("L", (nw, nh), 255)
    glyph = Image.merge("RGBA", (white, white, white, cropped_a))
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    canvas.paste(glyph, ((size - nw) // 2, (size - nh) // 2), glyph)
    r, g, b, a = canvas.split()
    a = a.point(lambda p: 0 if p < 24 else (255 if p > 160 else p))
    canvas = Image.merge("RGBA", (r, g, b, a))
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest, format="PNG", optimize=True)


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS,
        aws_secret_access_key=S3_SECRET,
        region_name="us-east-1",
    )


def ensure_bucket(client) -> None:
    try:
        client.head_bucket(Bucket=S3_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=S3_BUCKET)


def upload_png(client, path: Path, key: str) -> None:
    client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=path.read_bytes(),
        ContentType="image/png",
        CacheControl="public, max-age=86400",
    )


async def update_db(rows: list[tuple[str, str]]) -> None:
    conn = await asyncpg.connect(DSN)
    try:
        await conn.executemany(
            """
            UPDATE place_categories
            SET icon_url = $2, updated_at = NOW()
            WHERE code = $1 AND deleted = FALSE
            """,
            rows,
        )
    finally:
        await conn.close()


async def main() -> None:
    missing = [c for c in CATEGORY_CODES if not (ASSETS_DIR / f"{c}.png").is_file()]
    if missing:
        raise SystemExit(f"Нет PNG в {ASSETS_DIR}: {', '.join(missing)}")

    client = s3_client()
    ensure_bucket(client)
    db_rows: list[tuple[str, str]] = []
    for code in CATEGORY_CODES:
        path = ASSETS_DIR / f"{code}.png"
        key = f"{KEY_PREFIX}/{code}.png"
        upload_png(client, path, key)
        db_rows.append((code, key))
        print(f"  s3://{S3_BUCKET}/{key}")

    await update_db(db_rows)
    print(f"OK icons={len(db_rows)} → place_categories.icon_url")


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-raw",
        type=Path,
        default=None,
        help="Папка raw RGB (чёрный фон) — конвертировать в альфа-PNG в assets/",
    )
    args = parser.parse_args()
    if args.from_raw:
        raw_dir = args.from_raw
        for code in CATEGORY_CODES:
            src = raw_dir / f"{code}.png"
            if not src.is_file():
                raise SystemExit(f"Нет raw {src}")
            dest = ASSETS_DIR / f"{code}.png"
            to_mask_png(src, dest)
            print(f"  mask {dest.relative_to(REPO_ROOT)}")
    asyncio.run(main())
