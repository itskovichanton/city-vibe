# Auth — аутентификация и аккаунты

← [Оглавление](index.md) · [Conventions](conventions.md)

**Префикс:** `/auth/*`  
**Upstream:** auth-service (`http://localhost:8082`)  
**Прокси:** все методы `GET|POST|PUT|PATCH|DELETE` на `/auth/{path}`

Потоки: регистрация + OTP → создание user (saga) → JWT; логин + OTP; сброс пароля (3 шага); refresh/logout; Google Sign-In.

События в RabbitMQ (для notification-service): `auth.otp.requested`, `auth.user.registered`.

---

## Общие модели

### Request: `VerifyBody` (OTP)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| `challenge_id` | string | да | UUID из предыдущего challenge |
| `code` | string | да | Ровно **6** символов (цифры OTP) |

### Response: `ChallengeOut`

| Поле | Тип | Описание |
|------|-----|----------|
| `challenge_id` | string | ID челленджа |
| `channel` | string | `email` \| `sms` |
| `destination_masked` | string | Маскированный email/телефон |
| `expires_in` | int | TTL, сек (default 300) |

### Response: `TokensOut`

| Поле | Тип | Описание |
|------|-----|----------|
| `access_token` | string | JWT |
| `refresh_token` | string | Refresh (ротация при refresh) |
| `token_type` | string | `Bearer` |
| `expires_in` | int | TTL access |
| `user_id` | int \| null | ID профиля user-service |
| `account_id` | int \| null | ID auth-аккаунта |

---

## `POST /auth/register`

Старт регистрации. Создаёт **pending**-аккаунт, шлёт OTP на `identifier`.

### Rate limit

`auth.register` ≈ 20 запросов / окно.

### Body (`RegisterBody`)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| `name` | string | да | Отображаемое имя |
| `identifier` | string | да | Email или телефон (см. [conventions](conventions.md)) |
| `password` | string | да | Пароль (хеш argon2/pwdlib на сервере) |
| `city_id` | int | да | ID города из place-service |
| `accept_terms` | bool | да | Должен быть `true`, иначе ошибка |
| `gender` | enum `Gender` | да | `male` \| `female` |
| `birthdate` | date \| null | нет | `YYYY-MM-DD` |

### Поведение

1. Если `accept_terms != true` → ошибка «Необходимо принять условия использования».
2. Парсинг `identifier` → email/phone.
3. Если уже есть **active** identity → «Аккаунт с таким identifier уже существует».
4. Создаётся pending account + identity, пароль хешируется.
5. Создаётся OTP challenge `purpose=register`, событие `auth.otp.requested` → письмо/SMS.

### Response `200` — `ChallengeOut`

### Пример

```bash
curl -s http://localhost:8080/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Анна",
    "identifier": "anna@example.com",
    "password": "Secret123!",
    "city_id": 1,
    "accept_terms": true,
    "gender": "female",
    "birthdate": "1995-04-12"
  }'
```

### Ошибки (бизнес)

- Условия не приняты
- Identifier уже занят (active)
- Невалидный identifier / валидация FastAPI `422`

---

## `POST /auth/register/verify`

Подтверждение регистрации OTP → активация аккаунта, **синхронное создание user** (saga), выдача токенов.

### Rate limit

`auth.register.verify` ≈ 30.

### Body

`VerifyBody` (`challenge_id`, `code`).

### Поведение (saga `register.verify`)

1. Проверка challenge: существует, `purpose=register`, код совпадает.
2. Загрузка pending-аккаунта.
3. S2S `user-service` `POST /users` с `name`, `gender`, `auth_account_id`, `city_id`, `birthdate`.
4. При сбое после создания user — компенсация: soft-delete user.
5. Активация аккаунта (`status=active`, привязка `user_id`).
6. Событие `auth.user.registered` (welcome notification).
7. Удаление OTP challenge.
8. Выдача access + refresh (`TokensOut`).

### Response `200` — `TokensOut`

### Ошибки

- Challenge не найден / истёк
- Неверный тип challenge
- Неверный код
- Аккаунт не найден
- Ошибка создания user (с откатом saga)

---

## `POST /auth/login`

Старт логина: проверка пароля → OTP challenge `purpose=login`.

### Rate limit

`auth.login` ≈ 30.

### Body (`LoginBody`)

| Поле | Тип | Обяз. |
|------|-----|-------|
| `identifier` | string | да |
| `password` | string | да |

### Поведение

1. Поиск аккаунта по identity; должен быть `status=active`.
2. Verify пароля.
3. При любой ошибке аутентификации — одинаковое сообщение «Неверный логин или пароль» (без enumeration).
4. OTP challenge + `auth.otp.requested`.

### Response `200` — `ChallengeOut`

---

## `POST /auth/login/verify`

Подтверждение логина OTP → токены.

### Rate limit

`auth.login.verify` ≈ 30.

### Body

`VerifyBody`.

### Поведение

1. Verify challenge `purpose=login`.
2. Удаление challenge.
3. Issue tokens для `account_id` из challenge.

### Response `200` — `TokensOut`

---

## `POST /auth/otp/resend`

Повторная отправка OTP по существующему `challenge_id`.

### Rate limit

`auth.otp.resend` ≈ 10.

### Body (`ResendBody`)

| Поле | Тип | Обяз. |
|------|-----|-------|
| `challenge_id` | string | да |

### Поведение

1. Загрузка старого challenge; если нет → «Challenge не найден».
2. Новый challenge с тем же `purpose`, destination, `account_id`, `extra`.
3. Новое событие OTP (новый код).

> Старый `challenge_id` после resend может стать недействительным в зависимости от реализации store (создаётся новый id). Клиент должен использовать **новый** `challenge_id` из ответа.

### Response `200` — `ChallengeOut`

---

## `POST /auth/password/forgot`

Шаг 1 сброса пароля: запрос OTP на identifier.

### Rate limit

`auth.password.forgot` ≈ 10.

### Body (`ForgotBody`)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| `identifier` | string | да | Email / телефон |
| `channel` | string \| null | нет | Подсказка канала (`email` / `phone`); парсер всё равно смотрит на identifier |

### Поведение

- Если аккаунт **не найден** — всё равно возвращается «фейковый» `ChallengeOut` (случайный `challenge_id`), чтобы не раскрывать наличие пользователя. OTP при этом **не** отправляется.
- Если найден — реальный challenge `purpose=reset` + OTP.

### Response `200` — `ChallengeOut`

---

## `POST /auth/password/forgot/verify`

Шаг 2: проверка OTP сброса → выдача одноразового `reset_token`.

### Body

`VerifyBody`.

### Поведение

1. Verify challenge `purpose=reset`.
2. Генерация `reset_token` (`token_urlsafe(32)`).
3. Сохранение в OTP store как challenge `purpose=reset_confirm` с TTL.
4. Удаление исходного OTP challenge.

### Response `200`

```json
{
  "reset_token": "<opaque>",
  "expires_in": 300
}
```

(ответ может быть в обёртке `result`, см. conventions)

---

## `POST /auth/password/reset`

Шаг 3: установка нового пароля по `reset_token`.

### Body (`ResetBody`)

| Поле | Тип | Обяз. |
|------|-----|-------|
| `reset_token` | string | да |
| `new_password` | string | да |

### Поведение

1. Загрузка challenge по `reset_token`, `purpose` должен быть `reset_confirm`.
2. Обновление `password_hash` аккаунта.
3. Удаление reset-токена из store.

### Response `200`

```json
{ "ok": true }
```

### Ошибки

- Reset token недействителен / истёк
- Аккаунт не найден

---

## `POST /auth/token/refresh`

Обновление пары токенов (rotation).

### Body (`RefreshBody`)

| Поле | Тип | Обяз. |
|------|-----|-------|
| `refresh_token` | string | да |

### Поведение

1. Хеш refresh → поиск в БД.
2. Проверка expiry.
3. **Revoke** старого refresh.
4. Выдача новой пары access + refresh.

### Response `200` — `TokensOut`

### Ошибки

- Refresh token недействителен / просрочен / уже отозван

---

## `POST /auth/logout`

Инвалидация refresh-токена (logout на устройстве).

### Body

`RefreshBody` (`refresh_token`).

### Поведение

Revoke refresh по хешу. Идемпотентно с точки зрения клиента: повторный logout с тем же токеном безопасен.

### Response `200`

```json
{ "ok": true }
```

> Access JWT до истечения TTL формально ещё валиден (stateless). Для жёсткого logout нужен короткий TTL access или blacklist (сейчас не реализован).

---

## `POST /auth/social/google`

Вход / регистрация через Google ID Token (native Sign-In).

### Rate limit

`auth.social.google` ≈ 20.

### Body (`GoogleBody`)

| Поле | Тип | Обяз. | Описание |
|------|-----|-------|----------|
| `id_token` | string | да | Google OAuth2 ID token |
| `city_id` | int \| null | нет* | Нужен при **первой** регистрации |
| `name` | string \| null | нет | Иначе берётся из Google profile |
| `birthdate` | date \| null | нет | |
| `gender` | enum `Gender` \| null | нет | `male` \| `female` (default `male`) |

\*При первом входе без существующего OAuth-аккаунта `city_id` обычно обязателен бизнес-логикой онбординга (передаётся в create user).

### Поведение

1. Проверка `auth.google_client_ids` в конфиге; если пусто → «Google OAuth не настроен».
2. Verify `id_token` против каждого client id (Android/iOS/Web).
3. Поиск oauth (`google`, `sub`).
4. **Если новый:**
   - pending account + link oauth;
   - sync create user в user-service;
   - activate.
5. Issue tokens.

### Response `200` — `TokensOut`

### Ошибки

- Google OAuth не настроен
- Неверный Google token
- Ошибки создания user

### Конфиг

В `python/auth_service/config.yml`:

```yaml
auth:
  google_client_ids:
    - "<android-client-id>.apps.googleusercontent.com"
    - "<ios-client-id>.apps.googleusercontent.com"
```

Секрет JWT должен совпадать с gateway (`auth.jwt_secret`).

---

## Диаграмма типичных флоу

```
Register:  register → (OTP) → register/verify → Tokens
Login:     login    → (OTP) → login/verify    → Tokens
Forgot:    forgot   → (OTP) → forgot/verify   → reset_token → password/reset
Google:    social/google → Tokens (без OTP)
Session:   token/refresh | logout
```

## Связанные темы

- [users](users.md) — профиль создаётся при `register/verify` и Google
- [cities](cities.md) — `city_id` при регистрации
- [infra](infra.md) — health auth backend
