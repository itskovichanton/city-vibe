# Users — профиль пользователя

← [Оглавление](index.md) · [Conventions](conventions.md)

**Префикс:** `/users`, `/users/{path}`  
**Upstream:** user-service (`http://localhost:8081`)  
**Прокси:** `GET|POST|PUT|PATCH|DELETE`

Профиль создаётся обычно **из auth-service** при `register/verify` или Google (S2S).  
Мобилка затем читает/дополняет профиль по `user_id` из `TokensOut`.

На upstream почти все методы защищены `@require_s2s` + rate-limit + (для мутаций) `@idempotent`.

---

## Модель `UserOut` / `UserResponse`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | ID пользователя |
| `name` | string | Имя |
| `status` | string | Статус сущности (enum Status) |
| `gender` | enum `Gender` | `male` \| `female` |
| `short_bio` | string | Коротко о себе (онбординг шаг 1) |
| `long_bio` | string | Развёрнутое «о себе» (шаг 2) |
| `age` | int \| null | Возраст 1..120 |
| `avatar_url` | string \| null | URL в MinIO/S3 |
| `role` | string | По умолчанию `REGULAR` |
| `favorite_categories` | string[] | Коды категорий мест (`PlaceCategory`) |
| `onboarding_completed` | bool | Флаг завершения онбординга |
| `deleted` | bool | Soft-delete |
| `city_id` | int \| null | Город из place-service |
| `birthdate` | date \| null | `YYYY-MM-DD` |
| `auth_account_id` | int \| null | Связь с auth-аккаунтом |

---

## Онбординг (логика шагов)

| Шаг | Метод | Что делает |
|-----|-------|------------|
| 1 | `POST /users` | Создать профиль (имя, категории, город…) |
| 2 | `PUT /users/{id}/bio` | Длинное bio |
| 3 | `POST /users/{id}/onboarding/complete` | `onboarding_completed=true` |
| * | `POST /users/{id}/avatar` | Аватар (можно на любом шаге после create) |

При регистрации через auth шаг 1 часто уже выполнен сервером (sync create).

---

## `POST /users`

Создать пользователя (онбординг / S2S из auth).

### Защита (upstream)

- `@require_s2s`
- `@idempotent("users.create")`
- `@rate_limit("users.create", limit=30)`

### Body (`CreateUserBody`)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| `name` | string | да | Имя |
| `gender` | enum `Gender` | да | `male` \| `female` |
| `age` | int \| null | нет | 1..120 |
| `short_bio` | string | нет | Коротко о себе (default `""`) |
| `favorite_categories` | string[] | нет | Неизвестные коды категорий пропускаются |
| `city_id` | int \| null | нет | ID из `/cities` |
| `birthdate` | date \| null | нет | |
| `auth_account_id` | int \| null | нет | ID auth-аккаунта (ставит auth-service) |

### Response `200` — `UserOut`

### Пример

```bash
curl -s http://localhost:8080/users \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <access>' \
  -d '{
    "name": "Анна",
    "gender": "female",
    "city_id": 1,
    "short_bio": "Люблю кофе",
    "favorite_categories": ["CAFE", "PARK"],
    "auth_account_id": 42
  }'
```

> Прямой вызов без S2S-токена к user-service упадёт; через gateway успех зависит от того, прокидываются ли S2S-заголовки. Для мобилки основной путь создания — auth verify.

---

## `GET /users/{user_id}`

Получить профиль.

### Защита

- `@require_s2s`
- `@rate_limit("users.get", limit=120)`

### Path

| Параметр | Тип | Обяз. |
|----------|-----|-------|
| `user_id` | int | да |

### Response `200` — `UserOut`

### Ошибки

- Пользователь не найден → not found

### Пример

```bash
curl -s http://localhost:8080/users/1 | jq
```

---

## `PUT /users/{user_id}/bio`

Обновить развёрнутое bio (онбординг шаг 2).

### Защита

- `@require_s2s`
- `@idempotent("users.bio")`
- `@rate_limit("users.bio", limit=60)`

### Path

| Параметр | Тип |
|----------|-----|
| `user_id` | int |

### Body (`UpdateBioBody`)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| `long_bio` | string | да | Текст «о себе» |

### Response `200` — обновлённый `UserOut`

### Пример

```bash
curl -s -X PUT http://localhost:8080/users/1/bio \
  -H 'Content-Type: application/json' \
  -d '{"long_bio": "Гуляю по городу, ищу уютные места."}'
```

---

## `POST /users/{user_id}/onboarding/complete`

Завершить онбординг (шаг 3): выставляет `onboarding_completed=true`.

### Защита

- `@require_s2s`
- `@idempotent("users.onboarding.complete")`
- `@rate_limit("users.onboarding", limit=20)`

### Path

| Параметр | Тип |
|----------|-----|
| `user_id` | int |

### Body

Нет.

### Response `200` — `UserOut`

### Пример

```bash
curl -s -X POST http://localhost:8080/users/1/onboarding/complete
```

---

## `POST /users/{user_id}/avatar`

Загрузить аватарку в S3 (MinIO). Файл валидируется (`filetype` / infra upload helpers).

### Защита

- `@require_s2s`
- `@idempotent("users.avatar")`
- `@rate_limit("users.avatar", limit=10, window_sec=60)`

### Path

| Параметр | Тип |
|----------|-----|
| `user_id` | int |

### Body

`multipart/form-data`:

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| `file` | file | да | Изображение |

Ключ в storage: `avatars/{user_id}/…`

### Response `200` — `AvatarUploadOut`

| Поле | Тип | Описание |
|------|-----|----------|
| `avatar_url` | string | Публичный/доступный URL |
| `user` | UserOut | Профиль после обновления |

> В mobile OpenAPI схема ответа — `AvatarUploadOut`. Фактический presenter может вернуть обновлённый user в `result` (см. реализацию upload: после save вызывается get_user). Ориентируйтесь на живой ответ `/docs` user-service при интеграции.

### Пример

```bash
curl -s -X POST http://localhost:8080/users/1/avatar \
  -F 'file=@./avatar.jpg'
```

### Ошибки

- Пользователь не найден
- Невалидный / неподдерживаемый файл
- Ошибка MinIO

---

## `DELETE /users/{user_id}`

Soft-delete пользователя (`deleted=true`).  
Проксируется gateway; в агрегированной mobile OpenAPI может **отсутствовать** (не mobile-first).

### Защита

- `@require_s2s`

### Path

| Параметр | Тип |
|----------|-----|
| `user_id` | int |

### Response `200`

```json
{ "ok": true, "user_id": 1 }
```

### Ошибки

- Не найден → not found

### Использование

Компенсация saga при откате `register.verify`; админские/внутренние сценарии. Мобилке обычно не нужен.

---

## Связанные темы

- [auth](auth.md) — создание профиля при verify / Google, `user_id` в токенах
- [cities](cities.md) — `city_id`
- [conventions](conventions.md) — S2S, idempotency, JWT
