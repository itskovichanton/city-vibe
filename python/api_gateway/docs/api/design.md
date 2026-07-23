# Design — пины и темы чатов

← [Оглавление](index.md)

**Upstream:** design-service `:8085`  
**БД:** `cityvibe_design`  
Медиа (png/gif/фоны) — в S3; здесь хранятся метаданные и URL.

## Пины

| Method | Path |
|--------|------|
| GET | `/pin-styles` |
| GET | `/pin-styles/default` |
| GET | `/pin-styles/{id}` |

Поля: `code`, `name`, `image_url`, `gif_url`, `anchor_x`, `anchor_y`.

Seed: `code=default`.

## Темы чата

| Method | Path |
|--------|------|
| GET | `/chat-themes` |
| GET | `/chat-themes/default` |
| GET | `/chat-themes/{id}` |

Поля: `code`, `name`, `background_url`, `font_family`, `colors` (json).

Связь с местом: `places.pin_style_id` / `places.chat_theme_id` в place-service.
