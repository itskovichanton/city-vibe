-- Миграция 001: таблица городов

CREATE TABLE IF NOT EXISTS cities (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(128) NOT NULL UNIQUE,
    region      VARCHAR(255) NOT NULL DEFAULT '',
    lat         DOUBLE PRECISION,
    lng         DOUBLE PRECISION,
    is_major    BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    about       TEXT NOT NULL DEFAULT '',
    deleted     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_cities_major ON cities (is_major, sort_order) WHERE deleted = FALSE;
