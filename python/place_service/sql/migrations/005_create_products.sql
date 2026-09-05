-- Категории товаров/услуг и таблица products (принадлежат places).

CREATE TABLE IF NOT EXISTS product_categories (
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

CREATE INDEX IF NOT EXISTS ix_product_categories_active
    ON product_categories (is_active) WHERE deleted = FALSE;

CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    place_id        INTEGER      NOT NULL REFERENCES places (id),
    name            VARCHAR(255) NOT NULL,
    description     TEXT         NOT NULL DEFAULT '',
    price           NUMERIC(12, 2) NOT NULL,
    category_code   VARCHAR(64)  NOT NULL REFERENCES product_categories (code),
    schedule        JSONB,
    deleted         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_products_place
    ON products (place_id) WHERE deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_products_category
    ON products (category_code) WHERE deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_products_price
    ON products (price) WHERE deleted = FALSE;
CREATE INDEX IF NOT EXISTS ix_products_name_trgm
    ON products USING gin (name gin_trgm_ops);
