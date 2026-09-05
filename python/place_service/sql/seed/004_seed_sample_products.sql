-- Якоря для демо-поиска Миланы (Новосибирск). Идемпотентно по имени места/продукта.
-- Не сидит все NSK-места — только 5 площадок.

WITH nsk AS (
    SELECT id AS city_id
    FROM cities
    WHERE slug = 'novosibirsk' AND deleted = FALSE
    LIMIT 1
)
INSERT INTO places (
    name, about, category_code, owner_id, city_id, lat, lng, attrs, schedule
)
SELECT
    v.name,
    v.about,
    v.category_code,
    1,
    nsk.city_id,
    v.lat,
    v.lng,
    '{}'::jsonb,
    v.schedule::jsonb
FROM nsk
CROSS JOIN (
    VALUES
        (
            'Кафе Мечта',
            'Кофейня в центре: круассаны, капучино и комбо по цене одного кофе.',
            'cafes',
            55.0304,
            82.9206,
            '{"timezone":"Asia/Novosibirsk","periods":[{"weekday":0,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":1,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":2,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":3,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":4,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":5,"closed":false,"intervals":[{"open":"09:00","close":"23:00"}]},{"weekday":6,"closed":false,"intervals":[{"open":"09:00","close":"23:00"}]}],"exceptions":[],"events":[]}'
        ),
        (
            'Филармония',
            'Новосибирская филармония: камерные и джазовые вечера.',
            'concerts',
            55.0289,
            82.9218,
            '{"timezone":"Asia/Novosibirsk","periods":[],"exceptions":[],"events":[]}'
        ),
        (
            'StandUp NSK',
            'Стендап-клуб: открытые микрофоны и хедлайнеры.',
            'comedy_clubs',
            55.0412,
            82.9154,
            '{"timezone":"Asia/Novosibirsk","periods":[],"exceptions":[],"events":[]}'
        ),
        (
            'Stretch Gym',
            'Зал растяжки и групповых занятий. Гостевой визит — по записи.',
            'gyms',
            55.0501,
            82.9302,
            '{"timezone":"Asia/Novosibirsk","periods":[{"weekday":0,"closed":false,"intervals":[{"open":"07:00","close":"22:00"}]},{"weekday":1,"closed":false,"intervals":[{"open":"07:00","close":"22:00"}]},{"weekday":2,"closed":false,"intervals":[{"open":"07:00","close":"22:00"}]},{"weekday":3,"closed":false,"intervals":[{"open":"07:00","close":"22:00"}]},{"weekday":4,"closed":false,"intervals":[{"open":"07:00","close":"22:00"}]},{"weekday":5,"closed":false,"intervals":[{"open":"09:00","close":"20:00"}]},{"weekday":6,"closed":true,"intervals":[]}],"exceptions":[],"events":[]}'
        ),
        (
            'Ресторан Сибирский дворик',
            'Бизнес-ланч по будням и happy hour с 15:00.',
            'restaurants',
            55.0352,
            82.9108,
            '{"timezone":"Asia/Novosibirsk","periods":[{"weekday":0,"closed":false,"intervals":[{"open":"11:00","close":"23:00"}]},{"weekday":1,"closed":false,"intervals":[{"open":"11:00","close":"23:00"}]},{"weekday":2,"closed":false,"intervals":[{"open":"11:00","close":"23:00"}]},{"weekday":3,"closed":false,"intervals":[{"open":"11:00","close":"23:00"}]},{"weekday":4,"closed":false,"intervals":[{"open":"11:00","close":"23:00"}]},{"weekday":5,"closed":false,"intervals":[{"open":"12:00","close":"00:00"}]},{"weekday":6,"closed":false,"intervals":[{"open":"12:00","close":"00:00"}]}],"exceptions":[],"events":[]}'
        )
) AS v(name, about, category_code, lat, lng, schedule)
WHERE EXISTS (SELECT 1 FROM place_categories c WHERE c.code = v.category_code AND c.deleted = FALSE)
  AND NOT EXISTS (
      SELECT 1 FROM places x
      WHERE x.name = v.name AND x.deleted = FALSE
  );

-- Продукты якорей
INSERT INTO products (place_id, name, description, price, category_code, schedule)
SELECT
    p.id,
    v.name,
    v.description,
    v.price,
    v.category_code,
    v.schedule
FROM places p
JOIN (
    VALUES
        (
            'Кафе Мечта',
            'Комбо 2 кофе + круассан',
            'Два капучино и круассан по цене одного кофе.',
            250.00::numeric,
            'coffee',
            '{"timezone":"Asia/Novosibirsk","periods":[{"weekday":0,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":1,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":2,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":3,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":4,"closed":false,"intervals":[{"open":"08:00","close":"22:00"}]},{"weekday":5,"closed":false,"intervals":[{"open":"09:00","close":"23:00"}]},{"weekday":6,"closed":false,"intervals":[{"open":"09:00","close":"23:00"}]}],"exceptions":[],"events":[]}'::jsonb
        ),
        (
            'Кафе Мечта',
            'Капучино',
            'Классический капучино 300 мл.',
            250.00::numeric,
            'coffee',
            NULL::jsonb
        ),
        (
            'Stretch Gym',
            'Абонемент 8 посещений',
            'Зал и растяжка на 30 дней.',
            4500.00::numeric,
            'membership',
            NULL::jsonb
        )
) AS v(place_name, name, description, price, category_code, schedule)
  ON p.name = v.place_name AND p.deleted = FALSE
WHERE EXISTS (SELECT 1 FROM product_categories c WHERE c.code = v.category_code AND c.deleted = FALSE)
  AND NOT EXISTS (
      SELECT 1 FROM products x
      WHERE x.place_id = p.id AND x.name = v.name AND x.deleted = FALSE
  );

-- Разовые события (относительные даты) + nullable price
INSERT INTO products (place_id, name, description, price, category_code, schedule)
SELECT
    p.id,
    v.name,
    v.description,
    v.price,
    v.category_code,
    jsonb_build_object(
        'timezone', 'Asia/Novosibirsk',
        'periods', '[]'::jsonb,
        'exceptions', '[]'::jsonb,
        'events', jsonb_build_array(
            jsonb_build_object(
                'start', to_char(CURRENT_DATE + v.offset_days, 'YYYY-MM-DD') || 'T' || v.start_t,
                'end', to_char(CURRENT_DATE + v.offset_days, 'YYYY-MM-DD') || 'T' || v.end_t,
                'note', v.note
            )
        )
    )
FROM places p
JOIN (
    VALUES
        ('Филармония', 'Чарли Паркер', 'Вечер джаза: квинтет памяти Чарли Паркера.', 1500.00::numeric, 'concert', 30, '19:00:00', '22:00:00', 'Чарли Паркер'),
        ('StandUp NSK', 'Открытый микрофон', 'Новые комики, вход по билету.', 500.00::numeric, 'standup', 7, '20:00:00', '22:00:00', 'Open mic'),
        ('StandUp NSK', 'Хедлайнер пятницы', 'Сольный сет приглашённого комика.', 1200.00::numeric, 'standup', 14, '20:00:00', '22:30:00', 'Headline'),
        ('Stretch Gym', 'Гостевая растяжка', 'Разовое занятие 45 минут, цена — см. описание / бесплатный гостевой визит.', NULL::numeric, 'fitness_class', 1, '19:00:00', '19:45:00', 'Guest stretch')
) AS v(place_name, name, description, price, category_code, offset_days, start_t, end_t, note)
  ON p.name = v.place_name AND p.deleted = FALSE
WHERE EXISTS (SELECT 1 FROM product_categories c WHERE c.code = v.category_code AND c.deleted = FALSE)
  AND NOT EXISTS (
      SELECT 1 FROM products x
      WHERE x.place_id = p.id AND x.name = v.name AND x.deleted = FALSE
  );

-- Бизнес-ланч и happy hour (recurring periods)
INSERT INTO products (place_id, name, description, price, category_code, schedule)
SELECT
    p.id,
    v.name,
    v.description,
    v.price,
    v.category_code,
    v.schedule::jsonb
FROM places p
JOIN (
    VALUES
        (
            'Ресторан Сибирский дворик',
            'Бизнес-ланч',
            'Суп, горячее и салат. Пн–пт 12:00–16:00.',
            490.00,
            'ready_meals',
            '{"timezone":"Asia/Novosibirsk","periods":[{"weekday":0,"closed":false,"intervals":[{"open":"12:00","close":"16:00"}]},{"weekday":1,"closed":false,"intervals":[{"open":"12:00","close":"16:00"}]},{"weekday":2,"closed":false,"intervals":[{"open":"12:00","close":"16:00"}]},{"weekday":3,"closed":false,"intervals":[{"open":"12:00","close":"16:00"}]},{"weekday":4,"closed":false,"intervals":[{"open":"12:00","close":"16:00"}]}],"exceptions":[],"events":[]}'
        ),
        (
            'Ресторан Сибирский дворик',
            'Happy hour',
            'Скидка на закуски и напитки с 15:00.',
            350.00,
            'food',
            '{"timezone":"Asia/Novosibirsk","periods":[{"weekday":0,"closed":false,"intervals":[{"open":"15:00","close":"18:00"}]},{"weekday":1,"closed":false,"intervals":[{"open":"15:00","close":"18:00"}]},{"weekday":2,"closed":false,"intervals":[{"open":"15:00","close":"18:00"}]},{"weekday":3,"closed":false,"intervals":[{"open":"15:00","close":"18:00"}]},{"weekday":4,"closed":false,"intervals":[{"open":"15:00","close":"18:00"}]},{"weekday":5,"closed":false,"intervals":[{"open":"15:00","close":"18:00"}]}],"exceptions":[],"events":[]}'
        )
) AS v(place_name, name, description, price, category_code, schedule)
  ON p.name = v.place_name AND p.deleted = FALSE
WHERE EXISTS (SELECT 1 FROM product_categories c WHERE c.code = v.category_code AND c.deleted = FALSE)
  AND NOT EXISTS (
      SELECT 1 FROM products x
      WHERE x.place_id = p.id AND x.name = v.name AND x.deleted = FALSE
  );
