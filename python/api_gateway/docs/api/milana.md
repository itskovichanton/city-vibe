# Milana — NL-поиск мест и продуктов через ИИ-агента

← [Оглавление](index.md) · [places-search](places-search.md) · [products-search](products-search.md)

**Upstream:** milana-service `:8086` (проксируется gateway как `/milana/*`)

## Механика (вариант B)

1. **PLAN** — Милана знает мир (города + категории мест + категории продуктов) и раскладывает `q` на шаги `{domain, intent, category, place_name?, place_category?, why}`. `domain` = `place` | `product`. Именованное заведение («акции в кафе Мечта») → `place_name` + опционально `place_category=cafes`.
2. Для шагов `place` подтягиваются **compact** JSON Schema attrs; у продуктов схем нет.
3. **BUILD** — Милана пишет тела `POST /places/search` или `POST /products/search`. Имя места — в `place_name`, не только в `q`. Даты → `date_from`/`date_to` (events). LLM не выдумывает id.
4. Python: резолв `place_name` → `places/search` (`limit=1`) → `place_id`; нет места — шаг пустой. Между шагами копит `exclude_ids` / `exclude_place_ids`. Если есть `my_geo` и нет `sort_by` → `distance`. Продукты без `place_id` → `one_per_place=true`.
5. **MESSAGE** — тёплый текст от Миланы в поле `message`. Товары/услуги принадлежат местам.

Keyword-heuristic в Python **нет**. Нужен `DEEPSEEK_API_KEY`.

NL-вход остаётся `POST /milana/places/search` (клиент не ломаем); внутри шаги могут ходить в products.

Лог всего общения DeepSeek + place API: файл `logs/milana-agent-milana-service.txt` (`LoggerService.get_file_logger("milana-agent")`).

## Справочники мира

| Method | Описание |
|--------|----------|
| `GET /milana/world` | `{cities, categories, product_categories}` compact |
| `GET /milana/cities` | города `{id,name,slug,region,lat,lng}` |
| `GET /milana/categories` | категории мест `{code,title,title_en}` |
| `GET /milana/product-categories` | категории товаров/услуг `{code,title,title_en}` |
| `GET /milana/attr-schemas/{category_code}` | compact schema attrs места (без description) |

Source of truth: place-service `GET /cities`, `/categories`, `/product-categories`, `/attr-schemas/{code}?compact=true`.

## NL-поиск

**Method:** `POST /milana/places/search`

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `q` | да | Произвольный текст пожеланий |
| `city_id` | нет | Default `3` |
| `my_geo` | нет | `{lat, lng}` |
| `weekday` | нет | `0`=пн…`6`=вс |
| `timezone` | нет | IANA TZ (`Asia/Novosibirsk`) для now / events |
| `limit_per_step` | нет | default 5 |

### Ответ

```json
{
  "message": "Привет! Я Милана. Вот что нашлось для тебя... Удачи!",
  "plan": [
    {"domain": "place", "intent": "Театр", "category": "theaters", "why": "после работы спектакль"},
    {"domain": "product", "intent": "Кофе в Мечте", "category": "coffee", "place_name": "Мечта", "place_category": "cafes", "why": "акции в кафе"}
  ],
  "steps": [
    {
      "domain": "place",
      "intent": "Театр",
      "why": "после работы спектакль",
      "search": {"city_id": 3, "category": "theaters", "...": "..."},
      "total": 12,
      "places": [{"id": 1, "name": "...", "distance_m": 1200}],
      "products": []
    },
    {
      "domain": "product",
      "intent": "Йога",
      "why": "занятие вечером",
      "search": {"city_id": 3, "category": "yoga_class", "open_at": [{"weekday": 1, "intervals": [{"open": "19:00"}]}]},
      "total": 3,
      "places": [],
      "products": [{"id": 4, "name": "Хатха-йога вечер", "price": 700, "place": {"name": "..."}}]
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

# NL search (места и/или продукты внутри)
curl -s http://localhost:8080/milana/places/search \
  -H 'Content-Type: application/json' \
  -d '{
  "q": "хочу вечером йогу недорого, а потом поесть в ресторане недалеко с парковкой",
  "city_id": 3,
  "my_geo": {"lat": 54.924424, "lng": 82.999171},
  "weekday": 1
}'
```

Swagger: `http://localhost:8086/docs`
