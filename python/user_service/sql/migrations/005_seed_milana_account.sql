-- Служебный аккаунт ИИ-гида Миланы (полноценный user с role=MILANA).
INSERT INTO users (
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
SELECT
    'Милана',
    'Ваш персональный гид по городу',
    'Я подбираю лучшие места, события и скидки на основе ваших интересов.',
    'ACTIVE',
    'MILANA',
    TRUE,
    FALSE,
    'female'::gender,
    '{}'::varchar[]
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE role = 'MILANA' AND deleted = FALSE
);
