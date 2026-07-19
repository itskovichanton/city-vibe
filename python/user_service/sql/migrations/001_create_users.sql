-- Миграция 001: таблица пользователей и устройств
-- Применяется вручную или через Alembic (см. Makefile: migrate-user)

create TABLE IF NOT EXISTS users (
    id                    SERIAL PRIMARY KEY,
    name                  VARCHAR(255) NOT NULL,
    username              VARCHAR(255) UNIQUE,
    age                   INTEGER,
    short_bio             VARCHAR(500) NOT NULL DEFAULT '',
    long_bio              TEXT NOT NULL DEFAULT '',
    avatar_url            VARCHAR(1024),
    status                VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    role                  VARCHAR(32) NOT NULL DEFAULT 'REGULAR',
    favorite_categories   VARCHAR(64)[] NOT NULL DEFAULT '{}',
    onboarding_completed  BOOLEAN NOT NULL DEFAULT FALSE,
    deleted               BOOLEAN NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

create index IF NOT EXISTS ix_users_status ON users (status) WHERE deleted = FALSE;
create index IF NOT EXISTS ix_users_onboarding ON users (onboarding_completed) WHERE deleted = FALSE;

create TABLE IF NOT EXISTS user_devices (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users (id) ON delete CASCADE,
    device_model  VARCHAR(255) NOT NULL,
    push_token    VARCHAR(512) NOT NULL,
    platform      VARCHAR(32) NOT NULL,
    os_version    VARCHAR(64),
    app_version   VARCHAR(64),
    last_active   TIMESTAMPTZ,
    deleted       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

create index IF NOT EXISTS ix_user_devices_user_id ON user_devices (user_id);
