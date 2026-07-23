-- Расширения для гео-расстояний (стандартный Postgres contrib, без смены образа)
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;

-- Индекс по городу+категории для поиска
CREATE INDEX IF NOT EXISTS ix_places_city_category
    ON places (city_id, category_code)
    WHERE deleted = FALSE;

-- GIN по attrs для @> / ?| фильтров
CREATE INDEX IF NOT EXISTS ix_places_attrs_gin
    ON places USING GIN (attrs jsonb_path_ops)
    WHERE deleted = FALSE;

-- Индекс по имени (ILIKE) — trigram если есть, иначе btree на lower(name) не для substring.
-- pg_trgm ускоряет ILIKE '%...%'
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS ix_places_name_trgm
    ON places USING GIN (name gin_trgm_ops)
    WHERE deleted = FALSE;
