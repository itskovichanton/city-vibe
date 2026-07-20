-- Миграция 003: поля для интеграции с auth-service

ALTER TABLE users ADD COLUMN IF NOT EXISTS city_id INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS birthdate DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_account_id BIGINT UNIQUE;

CREATE INDEX IF NOT EXISTS ix_users_city_id ON users (city_id) WHERE deleted = FALSE;
