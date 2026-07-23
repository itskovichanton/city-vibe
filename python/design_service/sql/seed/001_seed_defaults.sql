-- Default pin + chat theme (id=1 ожидаем после чистого seed)
INSERT INTO map_pin_styles (code, name, image_url, gif_url, anchor_x, anchor_y)
VALUES (
    'default',
    'Default pin',
    'https://cdn.cityvibe.local/design/pins/default.png',
    NULL,
    0.5,
    1.0
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    image_url = EXCLUDED.image_url,
    updated_at = NOW();

INSERT INTO chat_themes (code, name, background_url, font_family, colors)
VALUES (
    'default',
    'Default chat theme',
    'https://cdn.cityvibe.local/design/chats/default-bg.jpg',
    'system',
    '{"primary":"#1A1A1A","accent":"#E8A838","background":"#F7F3EE","text":"#1A1A1A"}'::jsonb
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    background_url = EXCLUDED.background_url,
    colors = EXCLUDED.colors,
    updated_at = NOW();
