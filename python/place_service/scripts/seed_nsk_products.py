#!/usr/bin/env python3
"""
Большой демо-каталог products для мест Новосибирска.

Рестораны/суши/пицца — 1–10 блюд, часто бизнес-ланч и вечерняя скидка.
Залы — абонементы и иногда гостевое занятие на завтра.
Стендап/театры/концерты — разовые events через 7–30 дней.
Акции — обычные продукты (food/coffee/drinks) с periods, без категории promo.

Якоря 004 (Мечта, Филармония, StandUp NSK, Stretch Gym, Сибирский дворик)
не трогаем: их продукты не удаляем и новые не добавляем.

Повторный запуск: удаляет прошлый bulk-сид NSK и вставляет заново.

Usage (из корня репо):
  PYTHONPATH=. python python/place_service/scripts/seed_nsk_products.py
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "python" / "place_service" / "src"))

import asyncpg  # noqa: E402

DSN = "postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_places"
BATCH = 500
NSK_SLUG = "novosibirsk"
TZ = "Asia/Novosibirsk"

ANCHOR_PLACE_NAMES = (
    "Кафе Мечта",
    "Филармония",
    "StandUp NSK",
    "Stretch Gym",
    "Ресторан Сибирский дворик",
)

FOOD_VENUES = {
    "restaurants",
    "sushi",
    "pizza",
    "burgers",
    "street_food",
    "food_trucks",
}
CAFE_VENUES = {
    "cafes",
    "dessert_cafes",
    "bakeries",
    "coffee_roasters",
    "teahouses",
    "board_game_cafes",
    "pet_cafes",
}
BAR_VENUES = {
    "bars",
    "wine_bars",
    "brewpubs",
    "lounges",
    "rooftop_bars",
    "nightclubs",
    "hookah",
    "hookah_lounges",
    "karaoke",
}
GYM_VENUES = {"gyms", "sports", "swimming_pools", "climbing"}
YOGA_VENUES = {"yoga"}
DANCE_VENUES = {"dance_studios"}
COMEDY_VENUES = {"comedy_clubs"}
THEATER_VENUES = {"theaters"}
CONCERT_VENUES = {"concerts", "jazz_clubs"}
CINEMA_VENUES = {"cinema"}
EXHIBIT_VENUES = {"exhibitions", "museums", "art_galleries"}
BEAUTY_VENUES = {"beauty_salons", "barbershops", "spa", "saunas", "banya"}
LIGHT_OUTDOOR = {"parks", "viewpoints", "waterfronts", "playgrounds"}

# (name, description, category, price_lo, price_hi)  price_hi is None → always None
RESTAURANT_DISHES = [
    ("Борщ сибирский", "С говядиной, сметаной и чесночной пампушкой.", "food", 280, 450),
    ("Пельмени домашние", "Со сметаной или бульоном.", "food", 320, 520),
    ("Стейк рибай", "На гриле, с соусом и овощами.", "food", 890, 1600),
    ("Цезарь с курицей", "Классический салат с крутонами.", "food", 340, 520),
    ("Паста карбонара", "С беконом и пармезаном.", "food", 390, 590),
    ("Уха томлёная", "Из местной рыбы.", "food", 310, 480),
    ("Бефстроганов", "С картофельным пюре.", "food", 450, 690),
    ("Оливье", "По-домашнему, с варёной колбасой.", "food", 220, 360),
    ("Греческий салат", "Фета, оливки, огурцы.", "food", 280, 420),
    ("Куриные котлеты", "С гречкой и подливой.", "food", 330, 480),
    ("Том ям", "Острый суп с креветками.", "food", 420, 640),
    ("Плов", "С бараниной, по-узбекски.", "food", 380, 560),
    ("Блины с икрой", "Тонкие блины, красная икра.", "food", 490, 790),
    ("Вареники с вишней", "Со сметаной.", "food", 260, 390),
    ("Шашлык из свинины", "С луком и лавашом.", "food", 420, 680),
]

SUSHI_DISHES = [
    ("Филадельфия", "Лосось, сливочный сыр, огурец.", "food", 390, 590),
    ("Калифорния", "Краб, авокадо, тобико.", "food", 360, 540),
    ("Сет «Сибирь»", "40 кусочков, роллы дня.", "food", 1290, 2190),
    ("Нигири с лососем", "4 штуки.", "food", 320, 480),
    ("Острый ролл тунец", "Спайси-майо, кунжут.", "food", 410, 590),
    ("Мисо-суп", "С тофу и водорослями.", "food", 180, 280),
    ("Гунканы с угрём", "5 штук.", "food", 390, 560),
    ("Поке с лососем", "Рис, авакадо, соус поке.", "food", 490, 720),
    ("Эдамаме", "Соль и кунжутное масло.", "food", 190, 290),
    ("Темпура креветки", "Хрустящие, 6 шт.", "food", 420, 640),
]

PIZZA_DISHES = [
    ("Маргарита", "Томаты, моцарелла, базилик.", "food", 390, 590),
    ("Пепперони", "Острая колбаса, сыр.", "food", 450, 690),
    ("Четыре сыра", "Моцарелла, горгонзола, пармезан, чеддер.", "food", 490, 740),
    ("Гавайская", "Ветчина и ананас.", "food", 430, 640),
    ("Диабло", "Острый соус, пепперони, халапеньо.", "food", 470, 720),
    ("Карбонара пицца", "Бекон, сливочный соус.", "food", 480, 730),
    ("Цезарь пицца", "Курица, салат, пармезан.", "food", 460, 700),
    ("Детская", "Без острого, с кукурузой.", "food", 350, 490),
    ("Чесночные палочки", "К пицце, 8 шт.", "food", 190, 290),
    ("Тирамису", "Домашний десерт.", "food", 280, 420),
]

BURGER_DISHES = [
    ("Классический бургер", "Говядина, чеддер, соус домашний.", "food", 390, 560),
    ("Чизбургер двойной", "Две котлеты, бекон.", "food", 490, 720),
    ("Чикен бургер", "Хрустящая курица, салат.", "food", 360, 520),
    ("Веган бургер", "Котлета из нута, авокадо.", "food", 380, 540),
    ("Картофель фри", "С соусом на выбор.", "food", 160, 260),
    ("Наггетсы", "8 шт., кисло-сладкий соус.", "food", 220, 340),
    ("Милкшейк ванильный", "400 мл.", "drinks", 220, 320),
    ("Острые крылышки", "12 шт.", "food", 390, 560),
]

STREET_DISHES = [
    ("Шаурма классическая", "Курица, овощи, соус.", "food", 220, 340),
    ("Хот-дог", "С маринованным огурцом.", "food", 180, 280),
    ("Чебурек с мясом", "Сочный, из тандыра.", "food", 160, 250),
    ("Корн-дог", "В кляре.", "food", 170, 260),
    ("Картошка по-деревенски", "С паприкой.", "food", 150, 230),
    ("Лимонад домашний", "Мята и лайм.", "drinks", 120, 190),
    ("Самса", "С говядиной.", "food", 140, 220),
    ("Фондю в стаканчике", "Сыр и гренки.", "food", 210, 320),
]

CAFE_ITEMS = [
    ("Капучино", "Классический 300 мл.", "coffee", 180, 280),
    ("Латте", "С мягкой молочной пенкой.", "coffee", 190, 290),
    ("Американо", "Двойной эспрессо и вода.", "coffee", 140, 210),
    ("Раф ванильный", "Сливки и ваниль.", "coffee", 230, 340),
    ("Эспрессо", "30 мл.", "coffee", 110, 160),
    ("Круассан с миндалём", "Свежая выпечка.", "bakery_goods", 160, 260),
    ("Чизкейк нью-йорк", "Кусок.", "bakery_goods", 280, 420),
    ("Сырник", "Со сметаной и ягодами.", "bakery_goods", 220, 340),
    ("Какао", "На молоке, с маршмеллоу.", "drinks", 170, 250),
    ("Матча латте", "Японский чай.", "drinks", 240, 340),
    ("Комбо 2 кофе + круассан", "Два напитка и круассан по цене одного кофе.", "coffee", 250, 390),
    ("2 кофе по цене одного", "Акция на капучино и латте.", "coffee", 180, 280),
]

BAR_ITEMS = [
    ("Авторский коктейль", "Сезонный микс бармена.", "drinks", 420, 690),
    ("Негрони", "Джин, кампари, вермут.", "drinks", 450, 650),
    ("Пиво разливное", "0.5 л, локальная пивоварня.", "drinks", 220, 380),
    ("Вино бокал", "Красное или белое.", "drinks", 280, 480),
    ("Начос с сыром", "К пиву.", "food", 320, 480),
    ("Крылышки барные", "Острые, к пиву.", "food", 390, 560),
    ("Сет шотов", "4 шота на компанию.", "drinks", 490, 790),
    ("Безалкогольный мохито", "Мята, лайм, содовая.", "drinks", 220, 320),
]

MEMBERSHIPS = [
    ("Абонемент 8 посещений", "Зал на 30 дней, 8 визитов.", "membership", 3500, 5500),
    ("Абонемент 12 посещений", "Зал на 45 дней.", "membership", 4800, 7200),
    ("Безлимит на месяц", "Неограниченные групповые.", "membership", 5900, 9900),
    ("Разовое посещение", "Один вход в зал.", "membership", 500, 900),
    ("Персональная тренировка", "60 минут с тренером.", "personal_training", 1800, 3200),
]

YOGA_ITEMS = [
    ("Хатха-йога", "Групповое занятие 75 мин.", "yoga_class", 700, 1200),
    ("Виньяса", "Динамическая практика.", "yoga_class", 750, 1300),
    ("Йога для начинающих", "Мягкий вход.", "yoga_class", 600, 1100),
    ("Абонемент 8 занятий йоги", "На 30 дней.", "membership", 4200, 6800),
]

DANCE_ITEMS = [
    ("Contemporary", "Современный танец, 60 мин.", "dance_class", 800, 1400),
    ("Хип-хоп", "Группа open.", "dance_class", 700, 1200),
    ("Латина", "Сальса и бачата.", "dance_class", 750, 1300),
    ("Абонемент 8 занятий танцев", "На месяц.", "membership", 4500, 7200),
]

STANDUP_SHOWS = [
    ("Открытый микрофон", "Новые комики, вход по билету.", "standup", 400, 700),
    ("Хедлайнер пятницы", "Сольный сет приглашённого комика.", "standup", 900, 1800),
    ("Прогон нового часа", "Закрытый показ материала.", "standup", 600, 1200),
    ("Импровизация", "Игры со зрителем.", "standup", 500, 900),
    ("Женский стендап", "Линейка комикесс.", "standup", 700, 1400),
]

PLAYS = [
    ("Чайка", "Чехов. Вечерний спектакль.", "theater_ticket", 800, 2500),
    ("Вишнёвый сад", "Классика на большой сцене.", "theater_ticket", 900, 2800),
    ("Гамлет", "Шекспир в новой постановке.", "theater_ticket", 1000, 3200),
    ("Три сестры", "Драма в двух действиях.", "theater_ticket", 850, 2600),
    ("Ревизор", "Гоголь, комедия.", "theater_ticket", 700, 2200),
    ("Горе от ума", "Грибоедов.", "theater_ticket", 800, 2400),
    ("Дядя Ваня", "Камерная сцена.", "theater_ticket", 750, 2100),
]

CONCERTS = [
    ("Вечер джаза", "Квинтет, стандарты и авторское.", "concert", 900, 2500),
    ("Камерный концерт", "Струнный квартет.", "concert", 800, 2200),
    ("Симфонический вечер", "Большой зал.", "concert", 1200, 3500),
    ("Рок-вечер", "Кавер-сет и авторские.", "concert", 700, 1800),
    ("Фортепианный рецитал", "Соло, два отделения.", "concert", 1000, 2800),
    ("Блюз в полночь", "Гитара и гармоника.", "concert", 800, 1900),
]

MOVIES = [
    ("Сеанс: авторское кино", "Один сеанс, выбранный фильм недели.", "cinema_ticket", 350, 550),
    ("Сеанс: блокбастер", "Большой зал, вечер.", "cinema_ticket", 400, 650),
    ("Сеанс: семейный", "Дневной, 6+.", "cinema_ticket", 300, 480),
    ("Сеанс: ретро", "Классика на плёнке / цифре.", "cinema_ticket", 320, 500),
]

EXHIBITS = [
    ("Билет на постоянную экспозицию", "Вход на весь день.", "exhibition_ticket", 300, 700),
    ("Временная выставка", "Спецпроект месяца.", "exhibition_ticket", 400, 900),
    ("Экскурсия с гидом", "Группа 45 минут.", "exhibition_ticket", 500, 1100),
]

BEAUTY_ITEMS = [
    ("Стрижка", "Мытьё + укладка.", "haircut", 1200, 2800),
    ("Мужская стрижка", "Классика или фейд.", "haircut", 800, 1800),
    ("Маникюр", "С покрытием.", "manicure", 1500, 2800),
    ("Педикюр", "Аппаратный.", "manicure", 1800, 3200),
    ("SPA-ритуал", "90 минут, тело.", "spa_treatment", 3500, 6900),
    ("Массаж спины", "45 минут.", "massage", 1800, 3200),
    ("Оформление бровей", "Коррекция и окрашивание.", "beauty", 800, 1500),
]

SHOP_ITEMS = [
    ("Подарочный набор", "Локальный сувенир.", "gifts", 490, 1900),
    ("Букет дня", "Сезонные цветы.", "flowers", 1500, 4500),
    ("Бестселлер недели", "Книга по рекомендации продавца.", "books", 450, 1200),
    ("Корзина фермерских продуктов", "Овощи, сыр, мёд.", "grocery", 890, 2500),
    ("Футболка", "Базовый хлопок.", "clothes", 990, 2490),
    ("Кроссовки", "Повседневные.", "shoes", 3990, 8990),
    ("Наушники", "Беспроводные.", "electronics", 1990, 7990),
    ("Свеча и диффузор", "Для дома.", "home_goods", 690, 1890),
    ("Аксессуар дня", "Ремень / шарф / сумка.", "accessories", 790, 3990),
]

KIDS_ITEMS = [
    ("Детское занятие", "45 минут, 4–8 лет.", "kids_class", 500, 1100),
    ("Мастер-класс для детей", "Творчество, все материалы.", "workshop_session", 700, 1400),
]

WORKSHOP_ITEMS = [
    ("Мастер-класс", "2 часа, материалы включены.", "workshop_session", 1500, 3500),
    ("Гончарный круг", "Изделие с собой.", "workshop_session", 1800, 3900),
    ("Фотосессия 30 мин", "Студия, 15 кадров.", "photo_session", 2500, 5500),
]

GENERIC_FALLBACK = [
    ("Услуга дня", "Базовый оффер площадки.", "gifts", 300, 1500),
    ("Разовое посещение", "Вход / сеанс.", "membership", 400, 1200),
    ("Мастер-класс гостя", "Короткий формат.", "workshop_session", 800, 2500),
]


def _empty_events() -> list:
    return []


def _weekly(weekdays: list[int], open_t: str, close_t: str) -> dict:
    periods = [
        {
            "weekday": wd,
            "closed": False,
            "intervals": [{"open": open_t, "close": close_t}],
        }
        for wd in weekdays
    ]
    return {
        "timezone": TZ,
        "periods": periods,
        "exceptions": [],
        "events": _empty_events(),
    }


def _event(offset_days: int, start_t: str, end_t: str, note: str) -> dict:
    d = date.today() + timedelta(days=offset_days)
    start = start_t if len(start_t) == 8 else f"{start_t}:00"
    end = end_t if len(end_t) == 8 else f"{end_t}:00"
    return {
        "timezone": TZ,
        "periods": [],
        "exceptions": [],
        "events": [
            {
                "start": f"{d.isoformat()}T{start}",
                "end": f"{d.isoformat()}T{end}",
                "note": note,
            }
        ],
    }


def _hhmm_minutes(raw: str) -> int:
    parts = (raw or "23:00").split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _place_close(schedule: Any, default: str = "23:00") -> str:
    if not isinstance(schedule, dict):
        return default
    closes: list[str] = []
    for period in schedule.get("periods") or []:
        for interval in period.get("intervals") or []:
            close = interval.get("close")
            if close:
                closes.append(str(close)[:5])
    if not closes:
        return default
    return max(closes, key=_hhmm_minutes)


def _can_happy_hour(close: str) -> bool:
    minutes = _hhmm_minutes(close)
    if minutes < 12 * 60:
        return True
    return minutes > 15 * 60


def _money(rng: random.Random, lo: int, hi: int) -> Decimal:
    return Decimal(rng.randint(int(lo), int(hi)))


def _from_pool(
    rng: random.Random,
    pool: list[tuple],
    k: int,
) -> list[tuple[str, str, str, Decimal | None, dict | None]]:
    k = max(1, min(k, len(pool)))
    picked = rng.sample(pool, k)
    out = []
    for name, desc, cat, lo, hi in picked:
        price = None if hi is None else _money(rng, lo, hi)
        out.append((name, desc, cat, price, None))
    return out


def _row(
    place_id: int,
    name: str,
    description: str,
    category: str,
    price: Decimal | None,
    schedule: dict | None,
) -> tuple:
    return (
        place_id,
        name,
        description,
        price,
        category,
        json.dumps(schedule, ensure_ascii=False) if schedule else None,
    )


def _gen_food_venue(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    cat = place["category_code"]
    if cat == "sushi":
        pool = SUSHI_DISHES
    elif cat == "pizza":
        pool = PIZZA_DISHES
    elif cat == "burgers":
        pool = BURGER_DISHES
    elif cat in {"street_food", "food_trucks"}:
        pool = STREET_DISHES
    else:
        pool = RESTAURANT_DISHES
    n = rng.randint(1, 10)
    products = _from_pool(rng, pool, n)
    close = _place_close(place["schedule"])
    if rng.random() < 0.72:
        products.append(
            (
                "Бизнес-ланч",
                "Суп, горячее и салат. Пн–пт 12:00–16:00.",
                "ready_meals",
                _money(rng, 350, 590),
                _weekly([0, 1, 2, 3, 4], "12:00", "16:00"),
            )
        )
    if rng.random() < 0.55 and _can_happy_hour(close):
        products.append(
            (
                "После 21:00 скидка 50% на всё меню!",
                "Вечерняя акция: скидка на блюда с 15:00 до закрытия.",
                "food",
                _money(rng, 250, 490),
                _weekly(list(range(7)), "15:00", close),
            )
        )
    return [_pack(place["id"], p) for p in products]


def _pack(place_id: int, item: tuple) -> tuple:
    name, desc, cat, price, schedule = item
    return _row(place_id, name, desc, cat, price, schedule)


def _gen_cafe(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(2, 6)
    products = _from_pool(rng, CAFE_ITEMS, n)
    if rng.random() < 0.45:
        products.append(
            (
                "Комбо кофе и выпечка",
                "Напиток + круассан или сырник.",
                "coffee",
                _money(rng, 280, 420),
                _weekly(list(range(7)), "08:00", "20:00"),
            )
        )
    return [_pack(place["id"], p) for p in products]


def _gen_bar(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(2, 6)
    products = _from_pool(rng, BAR_ITEMS, n)
    close = _place_close(place["schedule"], "02:00")
    if rng.random() < 0.6 and _can_happy_hour(close):
        products.append(
            (
                "Happy hour",
                "Скидка на закуски и напитки с 15:00.",
                "drinks",
                _money(rng, 250, 450),
                _weekly([0, 1, 2, 3, 4, 5], "15:00", close if close != "02:00" else "18:00"),
            )
        )
    return [_pack(place["id"], p) for p in products]


def _gen_gym(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(2, 4)
    products = _from_pool(rng, MEMBERSHIPS, n)
    if rng.random() < 0.4:
        products.append(
            (
                "Гостевая растяжка",
                "Разовое занятие 45 минут, цена — см. описание / бесплатный гостевой визит.",
                "fitness_class",
                None,
                _event(1, "19:00:00", "19:45:00", "Guest stretch"),
            )
        )
    if rng.random() < 0.25:
        products.append(
            (
                "Утренняя зарядка",
                "Групповое 45 минут.",
                "fitness_class",
                _money(rng, 400, 800),
                _weekly([0, 1, 2, 3, 4], "07:30", "08:15"),
            )
        )
    return [_pack(place["id"], p) for p in products]


def _gen_yoga(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(2, 4)
    products = _from_pool(rng, YOGA_ITEMS, n)
    for i, p in enumerate(products):
        name, desc, cat, price, _ = p
        if cat == "yoga_class":
            start = rng.choice(["09:00", "12:00", "18:30", "19:30"])
            hh, mm = start.split(":")
            end_h = int(hh) + 1
            end = f"{end_h:02d}:{mm}"
            products[i] = (name, desc, cat, price, _weekly([0, 2, 4], start, end))
    return [_pack(place["id"], p) for p in products]


def _gen_dance(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(2, 4)
    products = _from_pool(rng, DANCE_ITEMS, n)
    for i, p in enumerate(products):
        name, desc, cat, price, _ = p
        if cat == "dance_class":
            products[i] = (
                name,
                desc,
                cat,
                price,
                _weekly([1, 3, 5], "19:00", "20:00"),
            )
    return [_pack(place["id"], p) for p in products]


def _gen_events_from_pool(
    place: asyncpg.Record,
    rng: random.Random,
    pool: list[tuple],
    k_lo: int,
    k_hi: int,
    offsets: list[int],
    start_t: str,
    end_t: str,
) -> list[tuple]:
    k = rng.randint(k_lo, min(k_hi, len(pool), len(offsets)))
    picked = rng.sample(pool, k)
    rows = []
    for i, (name, desc, cat, lo, hi) in enumerate(picked):
        rows.append(
            _pack(
                place["id"],
                (
                    name,
                    desc,
                    cat,
                    _money(rng, lo, hi),
                    _event(offsets[i], start_t, end_t, name),
                ),
            )
        )
    return rows


def _gen_beauty(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(2, 5)
    return [_pack(place["id"], p) for p in _from_pool(rng, BEAUTY_ITEMS, n)]


def _gen_shop(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    cat = place["category_code"]
    prefer = {
        "bookstores": "books",
        "libraries": "books",
        "flower_shops": "flowers",
        "farmers_markets": "grocery",
        "markets": "grocery",
        "malls": "clothes",
        "shopping": "clothes",
        "flea_markets": "gifts",
        "antique": "gifts",
    }.get(cat)
    pool = list(SHOP_ITEMS)
    if prefer:
        preferred = [x for x in pool if x[2] == prefer]
        rest = [x for x in pool if x[2] != prefer]
        pool = preferred + rest
    n = rng.randint(1, 4)
    return [_pack(place["id"], p) for p in _from_pool(rng, pool, n)]


def _gen_kids(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(1, 3)
    return [_pack(place["id"], p) for p in _from_pool(rng, KIDS_ITEMS, n)]


def _gen_workshop(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    n = rng.randint(1, 3)
    products = _from_pool(rng, WORKSHOP_ITEMS, n)
    for i, p in enumerate(products):
        name, desc, cat, price, _ = p
        if cat in {"workshop_session", "photo_session"}:
            products[i] = (
                name,
                desc,
                cat,
                price,
                _weekly([5, 6], "12:00", "18:00")
                if rng.random() < 0.5
                else _event(rng.choice([3, 7, 10]), "12:00:00", "15:00:00", name),
            )
    return [_pack(place["id"], p) for p in products]


def _gen_outdoor(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    if rng.random() < 0.45:
        return []
    n = rng.randint(1, 2)
    pool = [
        ("Прогулка с гидом", "Группа 60 минут по маршруту.", "education", 0, 500),
        ("Семейный пикник-набор", "Плед и термос напрокат.", "sport_rental", 300, 800),
        ("Детская площадка: занятие", "Аниматор 45 минут.", "kids_class", 400, 900),
        ("Летний фестиваль", "Разовая площадка на выходных.", "festival", 0, 700),
    ]
    products = _from_pool(rng, pool, n)
    for i, p in enumerate(products):
        name, desc, cat, price, _ = p
        if cat == "festival":
            products[i] = (
                name,
                desc,
                cat,
                price if price and price > 0 else None,
                _event(rng.choice([7, 14, 21]), "12:00:00", "20:00:00", name),
            )
        elif cat == "education":
            products[i] = (
                name,
                desc,
                cat,
                price if price and price > 0 else None,
                _weekly([5, 6], "11:00", "16:00"),
            )
    return [_pack(place["id"], p) for p in products]


def _gen_activity(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    cat = place["category_code"]
    titles = {
        "quests": ("Квест на двоих", "60 минут, сложность средняя.", "workshop_session", 2500, 4500),
        "escape_rooms": ("Комната: побег", "Команда до 6 человек.", "workshop_session", 2800, 5200),
        "bowling": ("Дорожка 1 час", "До 6 человек, обувь включена.", "sport_rental", 900, 1800),
        "billiards": ("Стол 60 минут", "Русская пирамида или пул.", "sport_rental", 500, 1100),
        "paintball": ("Игра 2 часа", "Маркер и костюм.", "sport_rental", 1800, 3200),
        "laser_tag": ("Сеанс лазертаг", "30 минут.", "sport_rental", 700, 1400),
        "karting": ("Заезд 10 минут", "Картинг, шлем включён.", "sport_rental", 900, 1600),
        "skating_rinks": ("Прокат коньков", "Сеанс 45 минут.", "sport_rental", 400, 800),
        "mini_golf": ("Партия мини-гольфа", "18 лунок.", "sport_rental", 500, 900),
        "vr_arenas": ("VR-сессия", "45 минут, 1 шлем.", "workshop_session", 900, 1800),
        "aquaparks": ("Входной билет", "Весь день, горки и бассейны.", "membership", 1200, 2500),
        "zoos": ("Входной билет", "Зоопарк, весь день.", "exhibition_ticket", 400, 900),
        "planetariums": ("Сеанс в планетарии", "Звёздное шоу 40 мин.", "exhibition_ticket", 350, 700),
        "coworking": ("Дневной тариф", "Рабочее место до вечера.", "membership", 600, 1400),
        "music_schools": ("Пробный урок", "45 минут, инструмент на месте.", "education", 800, 1600),
    }
    spec = titles.get(cat)
    rows = []
    if spec:
        name, desc, pcat, lo, hi = spec
        rows.append(_pack(place["id"], (name, desc, pcat, _money(rng, lo, hi), None)))
        if rng.random() < 0.5:
            rows.append(
                _pack(
                    place["id"],
                    (
                        f"{name} — вечер",
                        desc,
                        pcat,
                        _money(rng, lo, hi),
                        _weekly([4, 5, 6], "18:00", "22:00"),
                    ),
                )
            )
    else:
        rows.extend([_pack(place["id"], p) for p in _from_pool(rng, GENERIC_FALLBACK, rng.randint(1, 3))])
    return rows


def products_for_place(place: asyncpg.Record, rng: random.Random) -> list[tuple]:
    cat = place["category_code"]
    if cat in FOOD_VENUES:
        return _gen_food_venue(place, rng)
    if cat in CAFE_VENUES:
        return _gen_cafe(place, rng)
    if cat in BAR_VENUES:
        return _gen_bar(place, rng)
    if cat in GYM_VENUES:
        return _gen_gym(place, rng)
    if cat in YOGA_VENUES:
        return _gen_yoga(place, rng)
    if cat in DANCE_VENUES:
        return _gen_dance(place, rng)
    if cat in COMEDY_VENUES:
        return _gen_events_from_pool(
            place, rng, STANDUP_SHOWS, 1, 2, [7, 14], "20:00:00", "22:00:00"
        )
    if cat in THEATER_VENUES:
        return _gen_events_from_pool(
            place, rng, PLAYS, 1, 2, [10, 24], "19:00:00", "21:30:00"
        )
    if cat in CONCERT_VENUES:
        return _gen_events_from_pool(
            place, rng, CONCERTS, 1, 2, [7, 30], "19:00:00", "21:30:00"
        )
    if cat in CINEMA_VENUES:
        return _gen_events_from_pool(
            place, rng, MOVIES, 2, 4, [1, 2, 3, 5], "18:30:00", "21:00:00"
        )
    if cat in EXHIBIT_VENUES:
        return _gen_events_from_pool(
            place, rng, EXHIBITS, 1, 3, [3, 14, 28], "11:00:00", "19:00:00"
        )
    if cat in BEAUTY_VENUES:
        return _gen_beauty(place, rng)
    if cat in LIGHT_OUTDOOR:
        return _gen_outdoor(place, rng)
    if cat in {
        "children_centers",
        "playgrounds",
    }:
        return _gen_kids(place, rng)
    if cat in {"workshops", "pottery", "photo_studios"}:
        return _gen_workshop(place, rng)
    if cat in {
        "bookstores",
        "libraries",
        "flower_shops",
        "farmers_markets",
        "markets",
        "malls",
        "shopping",
        "flea_markets",
        "antique",
    }:
        return _gen_shop(place, rng)
    return _gen_activity(place, rng)


async def _insert_batch(conn: asyncpg.Connection, rows: list[tuple]) -> None:
    await conn.executemany(
        """
        INSERT INTO products (place_id, name, description, price, category_code, schedule)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        """,
        rows,
    )


async def main() -> None:
    rng = random.Random(42)
    conn = await asyncpg.connect(DSN)
    try:
        city_id = await conn.fetchval(
            "SELECT id FROM cities WHERE slug = $1 AND deleted = FALSE", NSK_SLUG
        )
        if city_id is None:
            raise SystemExit(f"City {NSK_SLUG} not found — run seed-place first")
        print(f"Novosibirsk city_id={city_id}")

        cats_ok = await conn.fetchval(
            "SELECT count(*) FROM product_categories WHERE deleted = FALSE"
        )
        if not cats_ok:
            raise SystemExit("product_categories empty — run make seed-place")

        deleted = await conn.execute(
            """
            DELETE FROM products p
            USING places pl
            WHERE p.place_id = pl.id
              AND pl.city_id = $1
              AND pl.name <> ALL($2::text[])
            """,
            city_id,
            list(ANCHOR_PLACE_NAMES),
        )
        print(f"cleared previous NSK bulk products: {deleted}")

        places = await conn.fetch(
            """
            SELECT id, name, category_code, schedule
            FROM places
            WHERE city_id = $1
              AND deleted = FALSE
              AND name <> ALL($2::text[])
            ORDER BY id
            """,
            city_id,
            list(ANCHOR_PLACE_NAMES),
        )
        print(f"places to seed: {len(places)}")

        batch: list[tuple] = []
        total = 0
        skipped_empty = 0
        for i, place in enumerate(places, start=1):
            rows = products_for_place(place, rng)
            if not rows:
                skipped_empty += 1
            batch.extend(rows)
            if len(batch) >= BATCH:
                await _insert_batch(conn, batch)
                total += len(batch)
                print(f"  inserted {total} products ({i}/{len(places)} places)")
                batch.clear()
        if batch:
            await _insert_batch(conn, batch)
            total += len(batch)

        all_count = await conn.fetchval(
            "SELECT count(*) FROM products WHERE deleted = FALSE"
        )
        nsk_count = await conn.fetchval(
            """
            SELECT count(*) FROM products p
            JOIN places pl ON pl.id = p.place_id
            WHERE p.deleted = FALSE AND pl.city_id = $1 AND pl.deleted = FALSE
            """,
            city_id,
        )
        dist = await conn.fetch(
            """
            SELECT p.category_code, count(*) AS n
            FROM products p
            JOIN places pl ON pl.id = p.place_id
            WHERE p.deleted = FALSE AND pl.city_id = $1 AND pl.deleted = FALSE
            GROUP BY p.category_code
            ORDER BY n DESC
            """,
            city_id,
        )
        print(f"OK inserted≈{total} nsk_products={nsk_count} all_products={all_count}")
        print(f"places without products (outdoor skip): {skipped_empty}")
        print("products by category_code:")
        for row in dist:
            print(f"  {row['category_code']}: {row['n']}")
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
