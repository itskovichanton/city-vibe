-- Категории мест, JSON Schema attrs, таблица places
CREATE TABLE IF NOT EXISTS place_categories (
    id            SERIAL PRIMARY KEY,
    code          VARCHAR(64)  NOT NULL UNIQUE,
    title         VARCHAR(255) NOT NULL,
    title_en      VARCHAR(255) NOT NULL DEFAULT '',
    icon_url      TEXT,
    sort_order    INTEGER      NOT NULL DEFAULT 0,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_place_categories_active
    ON place_categories (is_active) WHERE deleted = FALSE;

CREATE TABLE IF NOT EXISTS attr_schemas (
    id             SERIAL PRIMARY KEY,
    category_code  VARCHAR(64) NOT NULL UNIQUE REFERENCES place_categories(code),
    version        INTEGER     NOT NULL DEFAULT 1,
    json_schema    JSONB       NOT NULL,
    deleted        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS places (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    about           TEXT         NOT NULL,
    category_code   VARCHAR(64)  NOT NULL REFERENCES place_categories(code),
    owner_id        INTEGER      NOT NULL,
    city_id         INTEGER,
    lat             DOUBLE PRECISION NOT NULL,
    lng             DOUBLE PRECISION NOT NULL,
    attrs           JSONB        NOT NULL DEFAULT '{}'::jsonb,
    schedule        JSONB,
    pin_style_id    INTEGER,
    chat_theme_id   INTEGER,
    rating_up       INTEGER      NOT NULL DEFAULT 0,
    rating_down     INTEGER      NOT NULL DEFAULT 0,
    contacts        JSONB        NOT NULL DEFAULT '[]'::jsonb,
    deleted         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_places_owner ON places (owner_id) WHERE deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_places_category ON places (category_code) WHERE deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_places_geo ON places (lat, lng) WHERE deleted = FALSE;
