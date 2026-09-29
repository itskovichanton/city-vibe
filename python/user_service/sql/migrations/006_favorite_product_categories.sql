-- Интересы по товарам/услугам (отдельно от favorite_categories = места).
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS favorite_product_categories VARCHAR(64)[] NOT NULL DEFAULT '{}';
