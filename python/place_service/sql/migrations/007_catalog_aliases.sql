-- Синонимы и разговорные формулировки для catalog/match.
-- pg_trgm уже подключён в 003_search_extensions.sql

CREATE TABLE IF NOT EXISTS catalog_aliases (
    id            SERIAL PRIMARY KEY,
    catalog       VARCHAR(64)  NOT NULL,
    target_code   VARCHAR(64)  NOT NULL,
    alias         TEXT         NOT NULL,
    why           TEXT         NOT NULL DEFAULT '',
    weight        REAL         NOT NULL DEFAULT 1.0,
    deleted       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_catalog_aliases_key
    ON catalog_aliases (catalog, target_code, alias)
    WHERE deleted = FALSE;

CREATE INDEX IF NOT EXISTS ix_catalog_aliases_catalog
    ON catalog_aliases (catalog)
    WHERE deleted = FALSE;

CREATE INDEX IF NOT EXISTS ix_catalog_aliases_alias_trgm
    ON catalog_aliases USING gin (alias gin_trgm_ops)
    WHERE deleted = FALSE;
