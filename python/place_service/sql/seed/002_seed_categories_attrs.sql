-- Базовый bootstrap категорий (минимальные схемы).
-- Полный набор (~73 категории) + уникальные JSON Schema + 10k мест НСК:
--   make seed-nsk-places

INSERT INTO place_categories (code, title, title_en, sort_order, icon_url) VALUES
    ('bars', 'Бары', 'Bars', 10, 'place_categories/bars.png'),
    ('restaurants', 'Рестораны', 'Restaurants', 20, 'place_categories/restaurants.png'),
    ('cafes', 'Кафе', 'Cafes', 30, 'place_categories/cafes.png'),
    ('hookah', 'Кальянные', 'Hookah', 40, 'place_categories/hookah.png'),
    ('concerts', 'Концерты', 'Concerts', 50, 'place_categories/concerts.png'),
    ('theaters', 'Театры', 'Theaters', 60, 'place_categories/theaters.png'),
    ('parks', 'Парки', 'Parks', 70, 'place_categories/parks.png'),
    ('exhibitions', 'Выставки', 'Exhibitions', 80, 'place_categories/exhibitions.png'),
    ('sports', 'Спорт', 'Sports', 90, 'place_categories/sports.png'),
    ('shopping', 'Шопинг', 'Shopping', 100, 'place_categories/shopping.png'),
    ('cinema', 'Кино', 'Cinema', 110, 'place_categories/cinema.png'),
    ('nightclubs', 'Ночные клубы', 'Nightclubs', 120, 'place_categories/nightclubs.png')
ON CONFLICT (code) DO UPDATE SET
    title = EXCLUDED.title,
    title_en = EXCLUDED.title_en,
    sort_order = EXCLUDED.sort_order,
    icon_url = COALESCE(EXCLUDED.icon_url, place_categories.icon_url),
    updated_at = NOW();
