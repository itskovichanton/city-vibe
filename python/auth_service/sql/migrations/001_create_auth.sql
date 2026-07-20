-- Миграция 001: аккаунты, идентичности, OAuth, refresh-токены

CREATE TABLE IF NOT EXISTS accounts (
    id              SERIAL PRIMARY KEY,
    user_id         BIGINT UNIQUE,
    password_hash   VARCHAR(512) NOT NULL DEFAULT '',
    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    name            VARCHAR(255) NOT NULL DEFAULT '',
    birthdate       DATE,
    city_id         INTEGER,
    accept_terms    BOOLEAN NOT NULL DEFAULT FALSE,
    deleted         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS identities (
    id              SERIAL PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    type            VARCHAR(16) NOT NULL,
    value           VARCHAR(255) NOT NULL,
    verified        BOOLEAN NOT NULL DEFAULT FALSE,
    is_primary      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (type, value)
);

CREATE INDEX IF NOT EXISTS ix_identities_account ON identities (account_id);

CREATE TABLE IF NOT EXISTS oauth_accounts (
    id                  SERIAL PRIMARY KEY,
    account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    provider            VARCHAR(32) NOT NULL,
    provider_user_id    VARCHAR(255) NOT NULL,
    email               VARCHAR(255),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, provider_user_id)
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id              SERIAL PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    token_hash      VARCHAR(128) NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_account ON refresh_tokens (account_id);
