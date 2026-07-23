-- Пины карты и темы чатов
CREATE TABLE IF NOT EXISTS map_pin_styles (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(64)  NOT NULL UNIQUE,
    name        VARCHAR(255) NOT NULL,
    image_url   TEXT         NOT NULL,
    gif_url     TEXT,
    anchor_x    DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    anchor_y    DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    deleted     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_themes (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(64)  NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    background_url  TEXT         NOT NULL,
    font_family     VARCHAR(128) NOT NULL DEFAULT 'system',
    colors          JSONB        NOT NULL DEFAULT '{}'::jsonb,
    deleted         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
