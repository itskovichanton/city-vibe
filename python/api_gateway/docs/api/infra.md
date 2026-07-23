# Infra — служебные методы

← [Оглавление](index.md) · [Conventions](conventions.md)

Методы самой api-gateway (не проксируются).

---

## `GET /health`

Проверка живости gateway и доступности upstream HTTP backends.

### Upstream

Выполняется **на gateway**, дополнительно дергает:

| Backend | URL |
|---------|-----|
| auth | `{upstreams.auth}/health` → `http://localhost:8082/health` |
| users | `{upstreams.users}/health` → `http://localhost:8081/health` |
| places | `{upstreams.places}/health` → `http://localhost:8083/health` |
| design | `{upstreams.design}/health` → `http://localhost:8085/health` |

Timeout на каждый backend: **3 секунды**.

### Параметры

Нет.

### Headers

Не требуются.

### Успешный ответ `200`

```json
{
  "gateway": "ok",
  "backends": {
    "auth": "ok",
    "users": "ok",
    "cities": "ok"
  }
}
```

### Возможные значения `backends.*`

| Значение | Смысл |
|----------|-------|
| `"ok"` | HTTP status &lt; 500 |
| `"error"` | Ответ получен, но status ≥ 500 |
| `"down: …"` | Сеть / timeout / exception (текст ошибки в строке) |

`gateway` всегда `"ok"`, если сам эндпоинт ответил (процесс жив).

### Пример

```bash
curl -s http://localhost:8080/health | jq
```

### Заметки

- Не проверяет notification-service, Redis, Postgres, RabbitMQ напрямую — только HTTP health трёх проксируемых сервисов.
- Удобен для smoke после `make start-all` и для оркестраторов / IDE.
