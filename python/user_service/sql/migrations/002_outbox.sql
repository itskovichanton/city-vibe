-- Outbox для надёжной публикации событий (CITYVIBE_OUTBOX_ENABLED=true)
CREATE TABLE IF NOT EXISTS outbox_messages (
    id            SERIAL PRIMARY KEY,
    topic         VARCHAR(255) NOT NULL,
    payload       TEXT NOT NULL,
    event_type    VARCHAR(128) NOT NULL DEFAULT '',
    request_id    VARCHAR(64),
    published     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_outbox_published ON outbox_messages (published, id);
CREATE INDEX IF NOT EXISTS ix_outbox_topic ON outbox_messages (topic);
