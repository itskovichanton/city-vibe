#!/usr/bin/env python3
"""Upsert синонимов catalog_aliases из catalog_aliases_data.py."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "python" / "place_service" / "src"))

import asyncpg  # noqa: E402

from python.place_service.src.place_service.infra.catalog_aliases_data import (  # noqa: E402
    all_alias_rows,
)

DSN = "postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_places"
BATCH = 400


async def main() -> None:
    rows = all_alias_rows()
    conn = await asyncpg.connect(DSN)
    try:
        await conn.execute("DELETE FROM catalog_aliases WHERE deleted = FALSE")
        for i in range(0, len(rows), BATCH):
            chunk = rows[i : i + BATCH]
            await conn.executemany(
                """
                INSERT INTO catalog_aliases (catalog, target_code, alias, why, weight)
                VALUES ($1, $2, $3, $4, $5)
                """,
                chunk,
            )
        n = await conn.fetchval(
            "SELECT count(*) FROM catalog_aliases WHERE deleted = FALSE"
        )
        dist = await conn.fetch(
            """
            SELECT catalog, count(*) AS n
            FROM catalog_aliases WHERE deleted = FALSE
            GROUP BY catalog ORDER BY catalog
            """
        )
        print(f"OK catalog_aliases={n}")
        for row in dist:
            print(f"  {row['catalog']}: {row['n']}")
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
