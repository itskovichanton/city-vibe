-- Опциональный лог уведомлений

CREATE TABLE IF NOT EXISTS notification_log (
    id          SERIAL PRIMARY KEY,
    channel     VARCHAR(16) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    topic       VARCHAR(128) NOT NULL,
    payload     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
