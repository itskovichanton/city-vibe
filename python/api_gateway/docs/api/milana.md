# Milana — NL-поиск мест через ИИ-агента

← [Оглавление](index.md) · [places-search](places-search.md)

**Upstream:** milana-service `:8086` (проксируется gateway как `/milana/*`)

## Механика (вариант B)

1. **PLAN** — Милана знает мир (города + категории) и раскладывает `q` на шаги `{intent, category, why}`
2. Подтягиваются **compact** JSON Schema только для выбранных категорий
3. **BUILD** — Милана сама пишет тела `POST /places/search`
4. Python только исполняет search + валидирует
5. **MESSAGE** — тёплый текст от Миланы в поле `message`

Keyword-heuristic в Python **нет**. Нужен `DEEPSEEK_API_KEY`.

Лог всего общения DeepSeek + place API: файл `logs/milana-agent-milana-service.txt` (`LoggerService.get_file_logger("milana-agent")`).

## Справочники мира

| Method | Описание |
|--------|----------|
| `GET /milana/world` | `{cities, categories}` compact |
| `GET /milana/cities` | города `{id,name,slug,region,lat,lng}` |
| `GET /milana/categories` | `{code,title,title_en}` |
| `GET /milana/attr-schemas/{category_code}` | compact schema (без description) |

Source of truth: place-service `GET /cities`, `/categories`, `/attr-schemas/{code}?compact=true`.

## NL-поиск

**Method:** `POST /milana/places/search`

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `q` | да | Произвольный текст пожеланий |
| `city_id` | нет | Default `3` |
| `my_geo` | нет | `{lat, lng}` |
| `weekday` | нет | `0`=пн…`6`=вс |
| `limit_per_step` | нет | default 5 |

### Ответ

```json
{
  "message": "Привет! Я Милана. Вот что нашлось для тебя... Удачи!",
  "plan": [
    {"intent": "Театр", "category": "theaters", "why": "после работы спектакль"}
  ],
  "steps": [
    {
      "intent": "Театр",
      "why": "после работы спектакль",
      "search": {"city_id": 3, "category": "theaters", "...": "..."},
      "total": 12,
      "places": [{"id": 1, "name": "...", "distance_m": 1200}]
    }
  ],
  "model": "deepseek-chat",
  "used_llm": true
}
```

## DeepSeek ENV

```bash
export DEEPSEEK_API_KEY=sk-...
export DEEPSEEK_BASE_URL=https://api.deepseek.com
export DEEPSEEK_MODEL=deepseek-chat
export DEEPSEEK_MAX_TOKENS=4096
```

## Пример curl

```bash
# мир
curl -s http://localhost:8080/milana/world | jq

# NL search
curl -s http://localhost:8080/milana/places/search \
  -H 'Content-Type: application/json' \
  -d '{
  "q": "я хочу сначала после работы (а я работаю до 18:00 + час до центра) сходить в театр а потом пойти поесть в ресторане не делеко (там должен быть паркинг). После этого ночью уже хожу на набережной погулять.",
  "city_id": 3,
  "my_geo": {"lat": 54.924424, "lng": 82.999171},
  "weekday": 4
}'
```

Swagger: `http://localhost:8086/docs`
