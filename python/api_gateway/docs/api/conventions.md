# Conventions — общие соглашения API Gateway

← [Оглавление](index.md)

## Base URL

```
http://localhost:8080
```

Все пути ниже относительно этого хоста. Мобильное приложение ходит **только** на gateway.

## Формат ответа

Сервисы используют `JSONResultPresenterImpl`. Успешный ответ часто обёрнут:

```json
{
  "result": { ... }
}
```

Ошибки приходят через общий error-handler (`CoreException` → HTTP status + тело с `message` / `reason`). Конкретный статус зависит от типа ошибки (валидация → 422, not found → 404, бизнес-ошибка → обычно 400/500 по правилам presenter).

## Content-Type

| Тип запроса | Content-Type |
|-------------|--------------|
| JSON body | `application/json` |
| Загрузка аватара | `multipart/form-data` |

## JWT на gateway

Если клиент передаёт заголовок:

```http
Authorization: Bearer <access_token>
```

gateway **валидирует** JWT (`HS256`, секрет `auth.jwt_secret` из `config.yml`).  
Невалидный / просроченный токен → **`401`** `{"error":"invalid_token"}`.

Если заголовка нет — запрос пропускается дальше (опциональная проверка).  
Обязательность авторизации на уровне бизнес-методов определяется upstream (например, user-service требует S2S).

## Identifier (email / телефон)

Поле `identifier` в auth-методах — строка, которую парсер распознаёт как:

- **email** → канал OTP `email` (письмо через notification-service / SMTP / MailHog)
- **телефон** → канал OTP `sms` (через mock-notify `:8090`)

В ответах challenge адрес маскируется (`destination_masked`), например `j***@mail.com` / `+7***12`.

## OTP challenge

Типичный ответ после register / login / forgot / resend:

| Поле | Тип | Описание |
|------|-----|----------|
| `challenge_id` | string (UUID) | Идентификатор челленджа; нужен для verify / resend |
| `channel` | string | `email` или `sms` |
| `destination_masked` | string | Куда уйдёт код (маскировано) |
| `expires_in` | int | TTL в секундах (по умолчанию **300**) |

Код OTP — **6 цифр**. Хранится в Redis. Purpose челленджа должен совпадать с ожидаемым (`register` / `login` / `reset`).

## Токены (`TokensOut`)

| Поле | Тип | Описание |
|------|-----|----------|
| `access_token` | string | JWT access |
| `refresh_token` | string | Opaque refresh (хранится хеш в БД) |
| `token_type` | string | Обычно `Bearer` |
| `expires_in` | int | TTL access (сек), типично ~900 |
| `user_id` | int \| null | ID в user-service |
| `account_id` | int \| null | ID аккаунта в auth-service |

Refresh при обновлении **ротируется** (старый revoke → выдаётся новая пара).

## Rate limiting

На upstream-ах стоят декораторы `@rate_limit(...)`. Примеры лимитов (auth):

| Ключ | Лимит (примерно) |
|------|------------------|
| `auth.register` | 20 |
| `auth.login` | 30 |
| `auth.otp.resend` | 10 |
| `auth.password.forgot` | 10 |
| `auth.social.google` | 20 |

Users: `users.create` 30, `users.get` 120, `users.avatar` 10/мин и т.д.  
При превышении — ошибка rate-limit (см. infra rate-limit middleware).

## Idempotency (user-service)

Мутирующие методы users помечены `@idempotent(...)`. Клиент может слать заголовок идемпотентности (если включён флаг infra), чтобы повторы create/bio/avatar не дублировали эффект.

## S2S (user-service)

Прямые вызовы user-service требуют `@require_s2s` (токен из конфига `clients.*.auth.session_token`).  
Через gateway мобилка обычно не ходит в users «в обход» auth: профиль создаётся auth-service при verify / Google; дальше клиент использует user_id из токенов.

## Интерактивная схема

Полный список методов с моделями: [`schema/openapi/city-vibe-mobile.json`](../../../../schema/openapi/city-vibe-mobile.json)  
Пересборка: `make openapi-mobile`
