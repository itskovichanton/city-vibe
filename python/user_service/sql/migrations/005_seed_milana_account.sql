-- Служебный аккаунт ИИ-гида Миланы (id закреплён в config milana.user_id).
INSERT INTO users (
    id,
    name,
    short_bio,
    long_bio,
    status,
    role,
    onboarding_completed,
    deleted,
    gender,
    favorite_categories
)
VALUES (
    40,
    'Милана',
    'Ваш персональный гид по городу',
    'Я подбираю лучшие места, события и скидки на основе ваших интересов.',
    'ACTIVE',
    'ASSISTANT',
    TRUE,
    FALSE,
    'female'::gender,
    '{}'::varchar[]
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_bio = EXCLUDED.short_bio,
    long_bio = EXCLUDED.long_bio,
    status = EXCLUDED.status,
    role = EXCLUDED.role,
    onboarding_completed = EXCLUDED.onboarding_completed,
    deleted = EXCLUDED.deleted,
    gender = EXCLUDED.gender,
    favorite_categories = EXCLUDED.favorite_categories,
    updated_at = NOW();

SELECT setval(
    pg_get_serial_sequence('users', 'id'),
    GREATEST((SELECT COALESCE(MAX(id), 1) FROM users), 40)
);
