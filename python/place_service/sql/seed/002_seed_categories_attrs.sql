-- Seed категорий из PlaceCategory enum + пустые JSON Schema (additionalProperties)
INSERT INTO place_categories (code, title, title_en, sort_order) VALUES
    ('bars', 'Бары', 'Bars', 10),
    ('restaurants', 'Рестораны', 'Restaurants', 20),
    ('cafes', 'Кафе', 'Cafes', 30),
    ('hookah', 'Кальянные', 'Hookah', 40),
    ('concerts', 'Концерты', 'Concerts', 50),
    ('theaters', 'Театры', 'Theaters', 60),
    ('parks', 'Парки', 'Parks', 70),
    ('exhibitions', 'Выставки', 'Exhibitions', 80),
    ('sports', 'Спорт', 'Sports', 90),
    ('shopping', 'Шопинг', 'Shopping', 100),
    ('cinema', 'Кино', 'Cinema', 110),
    ('nightclubs', 'Ночные клубы', 'Nightclubs', 120)
ON CONFLICT (code) DO UPDATE SET
    title = EXCLUDED.title,
    title_en = EXCLUDED.title_en,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

INSERT INTO attr_schemas (category_code, version, json_schema)
SELECT c.code, 1, '{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "price_level": {"type": "integer", "minimum": 1, "maximum": 4},
    "has_wifi": {"type": "boolean"},
    "tags": {"type": "array", "items": {"type": "string"}}
  }
}'::jsonb
FROM place_categories c
WHERE c.deleted = FALSE
ON CONFLICT (category_code) DO NOTHING;
