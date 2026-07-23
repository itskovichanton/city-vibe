"""JSON Schema attrs по категориям. Все properties необязательные; у каждого есть description."""

from __future__ import annotations

from typing import Any, Dict

from python.libs.entities.place import PlaceCategory


def _obj(**properties: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }


def _enum(*values: str, description: str = "") -> Dict[str, Any]:
    s: Dict[str, Any] = {"type": "string", "enum": list(values)}
    if description:
        s["description"] = description
    return s


def _enum_arr(*values: str, description: str = "") -> Dict[str, Any]:
    s: Dict[str, Any] = {
        "type": "array",
        "items": {"type": "string", "enum": list(values)},
        "uniqueItems": True,
    }
    if description:
        s["description"] = description
    return s


def _bool(description: str = "") -> Dict[str, Any]:
    s: Dict[str, Any] = {"type": "boolean"}
    if description:
        s["description"] = description
    return s


def _int(min_v: int | None = None, max_v: int | None = None, description: str = "") -> Dict[str, Any]:
    s: Dict[str, Any] = {"type": "integer"}
    if min_v is not None:
        s["minimum"] = min_v
    if max_v is not None:
        s["maximum"] = max_v
    if description:
        s["description"] = description
    return s


def _str(description: str = "") -> Dict[str, Any]:
    s: Dict[str, Any] = {"type": "string"}
    if description:
        s["description"] = description
    return s


def _num(min_v: float | None = None, max_v: float | None = None, description: str = "") -> Dict[str, Any]:
    s: Dict[str, Any] = {"type": "number"}
    if min_v is not None:
        s["minimum"] = min_v
    if max_v is not None:
        s["maximum"] = max_v
    if description:
        s["description"] = description
    return s


def _int_enum(*values: int, description: str = "") -> Dict[str, Any]:
    s: Dict[str, Any] = {"type": "integer", "enum": list(values)}
    if description:
        s["description"] = description
    return s


CUISINES = (
    "vegetarian",
    "vegan",
    "pan_asian",
    "european",
    "russian",
    "georgian",
    "italian",
    "japanese",
    "chinese",
    "korean",
    "mexican",
    "middle_eastern",
    "seafood",
    "steakhouse",
    "fusion",
)

DRINKS = ("wine", "cocktails", "beer", "craft_beer", "whiskey", "coffee", "non_alcoholic", "shots")

COMMON_FOOD = {
    "price_level": _int(1, 4, description="Ценовой уровень заведения: 1 — бюджетно, 4 — премиум"),
    "has_wifi": _bool(description="Есть ли бесплатный Wi‑Fi для гостей"),
    "has_terrace": _bool(description="Есть ли летняя веранда / терраса"),
    "has_parking": _bool(description="Есть ли парковка для гостей"),
    "avg_bill_rub": _int(200, 15000, description="Средний чек на человека в рублях"),
    "reservation_required": _bool(description="Нужна ли предварительная бронь стола"),
}


CATEGORY_SCHEMAS: Dict[PlaceCategory, Dict[str, Any]] = {
    PlaceCategory.RESTAURANTS: _obj(
        **COMMON_FOOD,
        cuisine=_enum_arr(
            *CUISINES,
            description="Кухни заведения (можно несколько): вегетарианская, паназиатская, европейская и т.д.",
        ),
        michelin_mentioned=_bool(description="Упоминалось ли заведение в гидах уровня Michelin / аналогах"),
        chef_table=_bool(description="Есть ли шеф-стол / дегустационный сет"),
        kids_menu=_bool(description="Есть ли детское меню"),
        dress_code=_enum(
            "casual",
            "smart_casual",
            "formal",
            description="Дресс-код: повседневный, smart casual или формальный",
        ),
    ),
    PlaceCategory.CAFES: _obj(
        **COMMON_FOOD,
        cuisine=_enum_arr(
            "european",
            "russian",
            "vegetarian",
            "vegan",
            "dessert",
            description="Направления кухни / меню кафе",
        ),
        specialty_coffee=_bool(description="Спешелти-кофе (альтернатива, авторские напитки)"),
        laptop_friendly=_bool(description="Удобно ли работать с ноутбуком (розетки, тишина)"),
        pet_friendly=_bool(description="Можно ли приходить с питомцами"),
    ),
    PlaceCategory.BARS: _obj(
        price_level=_int(1, 4, description="Ценовой уровень: 1 — бюджетно, 4 — премиум"),
        has_wifi=_bool(description="Есть ли Wi‑Fi"),
        drinks=_enum_arr(*DRINKS, description="Основные напитки в меню: вино, коктейли, пиво и т.д."),
        has_happy_hour=_bool(description="Есть ли happy hour со скидками"),
        has_live_dj=_bool(description="Бывает ли живой DJ / музыкальная программа"),
        smoking_area=_bool(description="Есть ли зона для курения"),
        standing_only=_bool(description="Только стоячие места без столиков"),
    ),
    PlaceCategory.WINE_BARS: _obj(
        price_level=_int(1, 4, description="Ценовой уровень винной карты"),
        wine_regions=_enum_arr(
            "france",
            "italy",
            "spain",
            "georgia",
            "chile",
            "new_zealand",
            "russia",
            description="Регионы вин в карте",
        ),
        by_the_glass=_bool(description="Есть ли вина бокалами (не только бутылками)"),
        cheese_pairing=_bool(description="Есть ли сырные / гастрономические пейринги"),
        sommelier=_bool(description="Работает ли сомелье"),
    ),
    PlaceCategory.BREWPUBS: _obj(
        price_level=_int(1, 4, description="Ценовой уровень"),
        own_brewery=_bool(description="Собственная пивоварня на месте"),
        tap_count=_int(4, 40, description="Число кранов / сортов на розлив"),
        beer_styles=_enum_arr(
            "ipa",
            "lager",
            "stout",
            "wheat",
            "sour",
            "porter",
            description="Стили пива в ассортименте",
        ),
        kitchen=_bool(description="Есть ли кухня / закуски"),
    ),
    PlaceCategory.ROOFTOP_BARS: _obj(
        price_level=_int(1, 4, description="Ценовой уровень"),
        drinks=_enum_arr(*DRINKS, description="Типы напитков на крыше"),
        city_view=_bool(description="Есть ли вид на город"),
        heated_in_winter=_bool(description="Обогрев / работа зимой"),
        dress_code=_enum("casual", "smart_casual", description="Дресс-код для входа"),
    ),
    PlaceCategory.LOUNGES: _obj(
        price_level=_int(1, 4, description="Ценовой уровень"),
        drinks=_enum_arr(*DRINKS, description="Напитки в лаунже"),
        soft_seating=_bool(description="Мягкая посадка (диваны, кресла)"),
        private_rooms=_bool(description="Есть ли приватные комнаты"),
        age_limit=_int(18, 21, description="Возрастное ограничение для входа"),
    ),
    PlaceCategory.NIGHTCLUBS: _obj(
        price_level=_int(1, 4, description="Ценовой уровень (вход / бар)"),
        music_genres=_enum_arr(
            "techno",
            "house",
            "hiphop",
            "pop",
            "russian_pop",
            "rnb",
            description="Основные музыкальные жанры",
        ),
        dress_code=_enum("casual", "smart_casual", "club", description="Дресс-код клуба"),
        face_control=_bool(description="Есть ли фейс-контроль"),
        age_limit=_int(18, 21, description="Минимальный возраст"),
        dancefloor_size=_enum("small", "medium", "large", description="Размер танцпола"),
    ),
    PlaceCategory.HOOKAH: _obj(
        price_level=_int(1, 4, description="Ценовой уровень"),
        tobacco_brands=_enum_arr(
            "tangiers",
            "darkside",
            "musthave",
            "daily_hookah",
            "local",
            description="Бренды табака / смесей",
        ),
        lounge_style=_enum("classic", "modern", "oriental", description="Стиль интерьера"),
        food_menu=_bool(description="Есть ли кухня / закуски"),
        private_cabins=_bool(description="Есть ли отдельные кабинки"),
    ),
    PlaceCategory.HOOKAH_LOUNGES: _obj(
        price_level=_int(1, 4, description="Ценовой уровень"),
        vip_rooms=_bool(description="Есть ли VIP-комнаты"),
        ps5=_bool(description="Есть ли игровые консоли"),
        board_games=_bool(description="Есть ли настольные игры"),
        open_late=_bool(description="Работает ли допоздна / круглосуточно по ночам"),
    ),
    PlaceCategory.GYMS: _obj(
        has_pool=_bool(description="Есть ли бассейн"),
        has_sauna=_bool(description="Есть ли сауна / хамам"),
        has_group_classes=_bool(description="Есть ли групповые занятия"),
        has_personal_trainers=_bool(description="Доступны ли персональные тренеры"),
        twenty_four_seven=_bool(description="Работает ли 24/7"),
        crossfit=_bool(description="Есть ли зона / программы кроссфита"),
        monthly_price_rub=_int(1500, 15000, description="Ориентировочная цена абонемента в месяц, ₽"),
        floor_count=_int(1, 5, description="Число этажей клуба"),
    ),
    PlaceCategory.SPORTS: _obj(
        sport_types=_enum_arr(
            "football",
            "basketball",
            "volleyball",
            "tennis",
            "hockey",
            "running",
            description="Виды спорта на площадке / объекте",
        ),
        outdoor=_bool(description="Есть ли открытая площадка"),
        indoor=_bool(description="Есть ли крытый зал"),
        rental_equipment=_bool(description="Можно ли арендовать инвентарь"),
        lighting=_bool(description="Есть ли освещение для игры вечером"),
    ),
    PlaceCategory.SWIMMING_POOLS: _obj(
        lane_count=_int(3, 10, description="Число дорожек"),
        length_meters=_int_enum(25, 50, description="Длина чаши в метрах (обычно 25 или 50)"),
        heated=_bool(description="Подогрев воды"),
        open_air=_bool(description="Открытый бассейн"),
        kids_pool=_bool(description="Есть ли детская чаша"),
        sauna=_bool(description="Есть ли сауна при бассейне"),
    ),
    PlaceCategory.YOGA: _obj(
        styles=_enum_arr(
            "hatha",
            "vinyasa",
            "ashtanga",
            "yin",
            "hot_yoga",
            "kundalini",
            description="Стили йоги в студии",
        ),
        mats_provided=_bool(description="Выдают ли коврики"),
        beginners_welcome=_bool(description="Есть ли группы для начинающих"),
        online_classes=_bool(description="Есть ли онлайн-занятия"),
    ),
    PlaceCategory.CLIMBING: _obj(
        wall_height_m=_int(5, 20, description="Высота стены в метрах"),
        bouldering=_bool(description="Есть ли боулдеринг"),
        rope_routes=_bool(description="Есть ли трассы с верёвкой"),
        shoe_rental=_bool(description="Аренда скальных туфель"),
        difficulty_max=_enum("5a", "6a", "7a", "8a", description="Максимальная категория сложности трасс"),
    ),
    PlaceCategory.QUESTS: _obj(
        difficulty=_enum("easy", "medium", "hard", "extreme", description="Сложность квеста"),
        players_min=_int(2, 4, description="Минимальное число игроков"),
        players_max=_int(4, 12, description="Максимальное число игроков"),
        duration_min=_int(45, 120, description="Длительность прохождения, минут"),
        horror=_bool(description="Жанр хоррор / страшилка"),
        actors=_bool(description="Участвуют ли актёры"),
        age_limit=_int(6, 18, description="Минимальный возраст участников"),
    ),
    PlaceCategory.ESCAPE_ROOMS: _obj(
        difficulty=_enum("easy", "medium", "hard", description="Сложность комнаты"),
        rooms_count=_int(1, 10, description="Сколько комнат / сценариев на площадке"),
        theme=_enum(
            "horror",
            "detective",
            "fantasy",
            "sci_fi",
            "historical",
            description="Тематика сценария",
        ),
        language=_enum_arr("ru", "en", description="Языки проведения"),
    ),
    PlaceCategory.BOWLING: _obj(
        lanes=_int(4, 24, description="Число дорожек"),
        shoe_rental=_bool(description="Аренда обуви"),
        neon=_bool(description="Неоновый / glow-bowling"),
        cafe=_bool(description="Есть ли кафе / бар"),
        kids_bumpers=_bool(description="Бамперы для детей"),
    ),
    PlaceCategory.BILLIARDS: _obj(
        tables=_int(2, 20, description="Число столов"),
        table_types=_enum_arr(
            "russian",
            "american",
            "snooker",
            description="Типы столов / игр",
        ),
        bar=_bool(description="Есть ли бар"),
        hourly_rate_rub=_int(300, 2000, description="Стоимость часа аренды стола, ₽"),
    ),
    PlaceCategory.KARAOKE: _obj(
        private_rooms=_bool(description="Есть ли отдельные кабинки"),
        rooms_count=_int(1, 20, description="Число кабинок"),
        song_catalog_size=_enum("small", "medium", "huge", description="Размер каталога песен"),
        food_menu=_bool(description="Есть ли кухня"),
        price_level=_int(1, 4, description="Ценовой уровень"),
    ),
    PlaceCategory.SPA: _obj(
        massage=_bool(description="Есть ли массаж"),
        hammam=_bool(description="Есть ли хаммам"),
        pool=_bool(description="Есть ли бассейн"),
        couples_room=_bool(description="Есть ли парный кабинет"),
        membership=_bool(description="Есть ли абонементы / членство"),
        price_level=_int(1, 4, description="Ценовой уровень услуг"),
    ),
    PlaceCategory.SAUNAS: _obj(
        dry_sauna=_bool(description="Сухая сауна"),
        steam=_bool(description="Паровая / хаммам"),
        ice_plunge=_bool(description="Купель / ледяное погружение"),
        capacity=_int(4, 30, description="Вместимость, человек"),
        private_rent=_bool(description="Можно ли снять целиком приватно"),
    ),
    PlaceCategory.BANYA: _obj(
        wood_fired=_bool(description="Дровяная баня"),
        venik=_bool(description="Есть ли веники / парение"),
        font=_bool(description="Есть ли купель / купель на улице"),
        private=_bool(description="Приватный формат (не общая)"),
        capacity=_int(4, 40, description="Вместимость компании"),
    ),
    PlaceCategory.BEAUTY_SALONS: _obj(
        services=_enum_arr(
            "hair",
            "nails",
            "makeup",
            "brows",
            "lashes",
            "cosmetology",
            description="Услуги салона",
        ),
        walk_ins=_bool(description="Принимают ли без записи"),
        price_level=_int(1, 4, description="Ценовой уровень"),
    ),
    PlaceCategory.BARBERSHOPS: _obj(
        hot_towel=_bool(description="Есть ли hot towel / классический барбер-ритуал"),
        beard_trim=_bool(description="Стрижка / моделирование бороды"),
        walk_ins=_bool(description="Можно ли без записи"),
        price_level=_int(1, 4, description="Ценовой уровень"),
    ),
    PlaceCategory.MUSEUMS: _obj(
        topics=_enum_arr(
            "history",
            "art",
            "science",
            "tech",
            "local",
            "military",
            description="Тематические направления музея",
        ),
        ticket_price_rub=_int(0, 2000, description="Цена взрослого билета, ₽ (0 — бесплатно)"),
        audio_guide=_bool(description="Есть ли аудиогид"),
        free_day=_enum(
            "monday",
            "thursday",
            "sunday",
            "none",
            description="День бесплатного / льготного входа, если есть",
        ),
    ),
    PlaceCategory.EXHIBITIONS: _obj(
        medium=_enum_arr(
            "painting",
            "photo",
            "sculpture",
            "digital",
            "mixed",
            description="Медиа / техники экспозиции",
        ),
        temporary=_bool(description="Временная выставка (не постоянная)"),
        ticket_required=_bool(description="Нужен ли билет"),
    ),
    PlaceCategory.ART_GALLERIES: _obj(
        sale=_bool(description="Продаются ли работы"),
        contemporary=_bool(description="Современное искусство"),
        local_artists=_bool(description="Представлены ли местные художники"),
        opening_events=_bool(description="Проводятся ли вернисажи / открытия"),
    ),
    PlaceCategory.THEATERS: _obj(
        genres=_enum_arr(
            "drama",
            "comedy",
            "musical",
            "ballet",
            "opera",
            "children",
            description="Жанры репертуара",
        ),
        hall_capacity=_int(50, 2000, description="Вместимость зала"),
        subtitles=_bool(description="Есть ли субтитры / тифлокомментарий"),
    ),
    PlaceCategory.CONCERTS: _obj(
        venue_type=_enum("arena", "club", "hall", "open_air", description="Тип площадки"),
        capacity=_int(100, 15000, description="Вместимость площадки"),
        genres=_enum_arr(
            "rock",
            "pop",
            "classical",
            "electronic",
            "jazz",
            "folk",
            description="Типичные жанры концертов",
        ),
    ),
    PlaceCategory.CINEMA: _obj(
        screens=_int(1, 16, description="Число залов / экранов"),
        imax=_bool(description="Есть ли IMAX / аналог большого формата"),
        vip_hall=_bool(description="Есть ли VIP-зал"),
        food_allowed=_bool(description="Можно ли еду/напитки в зал"),
        formats=_enum_arr("2d", "3d", "atmos", description="Форматы показа"),
    ),
    PlaceCategory.PARKS: _obj(
        area_ha=_num(0.5, 500, description="Площадь парка в гектарах"),
        playground=_bool(description="Есть ли детская площадка"),
        lake=_bool(description="Есть ли озеро / водоём"),
        bike_paths=_bool(description="Есть ли велодорожки"),
        lighting=_bool(description="Вечернее освещение"),
        dogs_allowed=_bool(description="Можно ли гулять с собаками"),
    ),
    PlaceCategory.SHOPPING: _obj(
        store_types=_enum_arr(
            "fashion",
            "electronics",
            "home",
            "books",
            "gifts",
            description="Типы магазинов / ассортимент",
        ),
        price_level=_int(1, 4, description="Ценовой уровень"),
        parking=_bool(description="Есть ли парковка"),
    ),
    PlaceCategory.MALLS: _obj(
        floors=_int(1, 8, description="Число этажей ТРЦ"),
        food_court=_bool(description="Есть ли фудкорт"),
        cinema=_bool(description="Есть ли кинотеатр"),
        parking_spaces=_int(50, 5000, description="Число машиномест"),
        brands_count=_int(20, 400, description="Ориентировочное число брендов / магазинов"),
    ),
    PlaceCategory.MARKETS: _obj(
        indoor=_bool(description="Крытый рынок"),
        specialties=_enum_arr(
            "produce",
            "meat",
            "fish",
            "spices",
            "clothes",
            description="Основные специализации рядов",
        ),
        open_air=_bool(description="Открытая часть рынка"),
    ),
    PlaceCategory.FARMERS_MARKETS: _obj(
        organic_only=_bool(description="Только органика / фермерские продукты"),
        local_farms=_bool(description="Продукция местных хозяйств"),
        weekends_only=_bool(description="Работает только по выходным"),
    ),
    PlaceCategory.FLEA_MARKETS: _obj(
        vintage=_bool(description="Винтаж / секонд-хенд"),
        bargaining=_bool(description="Принят ли торг"),
        covered=_bool(description="Крытая площадка"),
    ),
    PlaceCategory.ANTIQUE: _obj(
        eras=_enum_arr(
            "soviet",
            "imperial",
            "mid_century",
            "asian",
            description="Эпохи / стили антиквариата",
        ),
        appraisal=_bool(description="Есть ли оценка / экспертиза"),
        price_level=_int(1, 4, description="Ценовой уровень"),
    ),
    PlaceCategory.BAKERIES: _obj(
        fresh_bread=_bool(description="Свежий хлеб собственной выпечки"),
        pastry=_bool(description="Выпечка / кондитерка"),
        gluten_free=_bool(description="Есть ли безглютеновые позиции"),
        seating=_bool(description="Есть ли посадочные места"),
        price_level=_int(1, 3, description="Ценовой уровень"),
    ),
    PlaceCategory.STREET_FOOD: _obj(
        cuisine=_enum_arr(*CUISINES, description="Кухни стритфуда"),
        seating=_bool(description="Есть ли столики / сиденья"),
        late_night=_bool(description="Работает ли поздно ночью"),
        price_level=_int(1, 2, description="Ценовой уровень (обычно бюджетный)"),
    ),
    PlaceCategory.SUSHI: _obj(
        price_level=_int(1, 4, description="Ценовой уровень"),
        delivery=_bool(description="Есть ли доставка"),
        omakase=_bool(description="Есть ли омакасе / сет от шефа"),
        conveyor=_bool(description="Конвейерная лента"),
        has_wifi=_bool(description="Есть ли Wi‑Fi"),
    ),
    PlaceCategory.PIZZA: _obj(
        oven=_enum("wood", "electric", "gas", description="Тип печи"),
        naples_style=_bool(description="Неаполитанская пицца"),
        delivery=_bool(description="Есть ли доставка"),
        price_level=_int(1, 4, description="Ценовой уровень"),
    ),
    PlaceCategory.BURGERS: _obj(
        smash=_bool(description="Готовят ли smash-бургеры"),
        vegetarian_patty=_bool(description="Есть ли вегетарианская котлета"),
        craft_soda=_bool(description="Есть ли крафтовые напитки / лимонады"),
        price_level=_int(1, 3, description="Ценовой уровень"),
    ),
    PlaceCategory.DESSERT_CAFES: _obj(
        specialties=_enum_arr(
            "cakes",
            "macarons",
            "ice_cream",
            "waffles",
            "chocolate",
            description="Специализация десертов",
        ),
        coffee=_bool(description="Есть ли кофейня / кофейная карта"),
        price_level=_int(1, 4, description="Ценовой уровень"),
    ),
    PlaceCategory.TEAHOUSES: _obj(
        tea_types=_enum_arr(
            "green",
            "black",
            "oolong",
            "puer",
            "herbal",
            description="Типы чая в меню",
        ),
        ceremony=_bool(description="Проводят ли чайные церемонии"),
        sweets=_bool(description="Есть ли сладости к чаю"),
        quiet=_bool(description="Тихая / медитативная атмосфера"),
    ),
    PlaceCategory.COFFEE_ROASTERS: _obj(
        own_roast=_bool(description="Собственная обжарка зерна"),
        pour_over=_bool(description="Есть ли альтернатива / пуровер"),
        beans_for_sale=_bool(description="Продают ли зерно с собой"),
        tasting=_bool(description="Проводят ли каппинги / дегустации"),
    ),
    PlaceCategory.FOOD_TRUCKS: _obj(
        cuisine=_enum_arr(*CUISINES, description="Кухня фудтрака"),
        mobile=_bool(description="Передвигается ли по городу"),
        fixed_spot=_bool(description="Стоит ли на постоянной точке"),
        price_level=_int(1, 2, description="Ценовой уровень"),
    ),
    PlaceCategory.PAINTBALL: _obj(
        outdoor=_bool(description="Открытая площадка"),
        indoor=_bool(description="Крытая арена"),
        scenarios=_bool(description="Есть ли сценарные игры"),
        rental_included=_bool(description="Экипировка входит в цену"),
        field_size=_enum("small", "medium", "large", description="Размер поля"),
    ),
    PlaceCategory.KARTING: _obj(
        track_length_m=_int(200, 1200, description="Длина трассы в метрах"),
        indoor=_bool(description="Закрытая трасса"),
        electric_karts=_bool(description="Электрические карты"),
        min_age=_int(6, 16, description="Минимальный возраст для заезда"),
    ),
    PlaceCategory.SKATING_RINKS: _obj(
        outdoor=_bool(description="Открытый каток"),
        skate_rental=_bool(description="Прокат коньков"),
        hockey=_bool(description="Возможен ли хоккей / тренировки"),
        music=_bool(description="Есть ли музыкальное сопровождение"),
    ),
    PlaceCategory.DANCE_STUDIOS: _obj(
        styles=_enum_arr(
            "ballet",
            "hiphop",
            "contemporary",
            "latin",
            "ballroom",
            "breakdance",
            description="Стили танцев",
        ),
        beginners=_bool(description="Есть ли группы для начинающих"),
        kids_groups=_bool(description="Есть ли детские группы"),
    ),
    PlaceCategory.JAZZ_CLUBS: _obj(
        live_every_night=_bool(description="Живая музыка почти каждый вечер"),
        dinner=_bool(description="Есть ли ужин / кухня во время концерта"),
        cover_charge=_bool(description="Есть ли входной / cover charge"),
        price_level=_int(1, 4, description="Ценовой уровень"),
    ),
    PlaceCategory.COMEDY_CLUBS: _obj(
        open_mic=_bool(description="Есть ли open mic"),
        food=_bool(description="Есть ли еда / бар"),
        age_limit=_int(16, 18, description="Возрастное ограничение"),
        price_level=_int(1, 4, description="Ценовой уровень билетов"),
    ),
    PlaceCategory.BOOKSTORES: _obj(
        genres=_enum_arr(
            "fiction",
            "nonfiction",
            "comics",
            "kids",
            "academic",
            description="Основные жанровые разделы",
        ),
        cafe=_bool(description="Есть ли кафе при магазине"),
        events=_bool(description="Проводят ли встречи / презентации"),
        used_books=_bool(description="Есть ли букинистика"),
    ),
    PlaceCategory.LIBRARIES: _obj(
        reading_rooms=_bool(description="Есть ли читальные залы"),
        coworking=_bool(description="Можно ли работать как в коворкинге"),
        kids_section=_bool(description="Есть ли детский отдел"),
        digital_access=_bool(description="Есть ли электронный каталог / доступ онлайн"),
    ),
    PlaceCategory.COWORKING: _obj(
        hot_desks=_bool(description="Есть ли hot desk"),
        private_offices=_bool(description="Есть ли кабинеты"),
        meeting_rooms=_int(1, 20, description="Число переговорных"),
        printing=_bool(description="Есть ли печать / сканер"),
        day_pass_rub=_int(300, 3000, description="Цена дневного пасса, ₽"),
        twenty_four_seven=_bool(description="Доступ 24/7"),
    ),
    PlaceCategory.BOARD_GAME_CAFES: _obj(
        games_count=_int(50, 2000, description="Число настольных игр в коллекции"),
        masters=_bool(description="Есть ли мастера / ведущие"),
        food=_bool(description="Есть ли кухня / бар"),
        price_per_hour_rub=_int(100, 500, description="Цена часа пребывания, ₽"),
    ),
    PlaceCategory.PET_CAFES: _obj(
        animals=_enum_arr(
            "cats",
            "dogs",
            "rabbits",
            "hedgehogs",
            "birds",
            description="Какие животные живут в кафе",
        ),
        adoption=_bool(description="Можно ли взять животное из приюта / на адаптацию"),
        food=_bool(description="Есть ли меню для гостей"),
        price_level=_int(1, 3, description="Ценовой уровень"),
    ),
    PlaceCategory.VR_ARENAS: _obj(
        stations=_int(2, 20, description="Число VR-станций"),
        free_roam=_bool(description="Есть ли free-roam арена"),
        games=_enum_arr("shooter", "horror", "racing", "coop", description="Жанры игр"),
        age_limit=_int(7, 16, description="Минимальный возраст"),
    ),
    PlaceCategory.LASER_TAG: _obj(
        arena_count=_int(1, 5, description="Число арен"),
        multi_level=_bool(description="Многоуровневая арена"),
        party_packages=_bool(description="Пакеты для дней рождения / корпоративов"),
    ),
    PlaceCategory.AQUAPARKS: _obj(
        slides=_int(3, 40, description="Число горок"),
        wave_pool=_bool(description="Есть ли волновой бассейн"),
        kids_zone=_bool(description="Есть ли детская зона"),
        indoor=_bool(description="Крытый аквапарк"),
        ticket_price_rub=_int(500, 5000, description="Цена взрослого билета, ₽"),
    ),
    PlaceCategory.ZOOS: _obj(
        animals_count=_int(20, 500, description="Ориентировочное число животных / видов"),
        petting_zoo=_bool(description="Есть ли контактный зоопарк"),
        feeding_shows=_bool(description="Есть ли шоу кормления"),
        ticket_price_rub=_int(200, 2000, description="Цена билета, ₽"),
    ),
    PlaceCategory.PLANETARIUMS: _obj(
        dome=_bool(description="Есть ли купольный зал"),
        fulldome=_bool(description="Fulldome / полнокупольные сеансы"),
        lectures=_bool(description="Есть ли лекции / научпоп"),
        kids_programs=_bool(description="Есть ли программы для детей"),
    ),
    PlaceCategory.PHOTO_STUDIOS: _obj(
        interior_sets=_int(1, 20, description="Число интерьерных локаций / сетов"),
        cyclorama=_bool(description="Есть ли циклорама"),
        equipment_rental=_bool(description="Аренда света / оборудования"),
        makeup_room=_bool(description="Есть ли гримёрка"),
        hourly_rate_rub=_int(1000, 10000, description="Цена часа аренды, ₽"),
    ),
    PlaceCategory.WORKSHOPS: _obj(
        crafts=_enum_arr(
            "wood",
            "metal",
            "jewelry",
            "leather",
            "print",
            description="Виды ремёсел / мастерских",
        ),
        drop_in=_bool(description="Можно ли прийти на разовое занятие"),
        courses=_bool(description="Есть ли курсы / абонементы"),
        materials_included=_bool(description="Материалы входят в стоимость"),
    ),
    PlaceCategory.POTTERY: _obj(
        wheel=_bool(description="Есть ли гончарный круг"),
        kiln=_bool(description="Есть ли обжиг / печь"),
        glaze=_bool(description="Глазурование / роспись"),
        kids_classes=_bool(description="Есть ли детские занятия"),
        price_per_session_rub=_int(800, 5000, description="Цена одного занятия, ₽"),
    ),
    PlaceCategory.FLOWER_SHOPS: _obj(
        delivery=_bool(description="Есть ли доставка букетов"),
        bouquets=_bool(description="Собирают ли букеты на заказ"),
        plants=_bool(description="Продают ли комнатные растения"),
        workshop=_bool(description="Есть ли мастер-классы по флористике"),
    ),
    PlaceCategory.MUSIC_SCHOOLS: _obj(
        instruments=_enum_arr(
            "piano",
            "guitar",
            "violin",
            "drums",
            "vocal",
            description="Инструменты / направления обучения",
        ),
        kids=_bool(description="Обучение детей"),
        adults=_bool(description="Обучение взрослых"),
        exams=_bool(description="Есть ли экзамены / аттестация"),
    ),
    PlaceCategory.MINI_GOLF: _obj(
        holes=_int(9, 18, description="Число лунок"),
        indoor=_bool(description="Закрытый мини-гольф"),
        themed=_bool(description="Тематические препятствия / декор"),
        cafe=_bool(description="Есть ли кафе"),
    ),
    PlaceCategory.WATERFRONTS: _obj(
        walking=_bool(description="Удобно ли для прогулок"),
        bike=_bool(description="Можно ли кататься на велосипеде / самокате"),
        cafes_nearby=_bool(description="Есть ли кафе рядом"),
        lighting=_bool(description="Вечернее освещение"),
        boat_rent=_bool(description="Аренда лодок / катамаранов"),
    ),
    PlaceCategory.VIEWPOINTS: _obj(
        height_m=_int(10, 200, description="Высота обзора в метрах"),
        paid=_bool(description="Платный вход"),
        sunset_popular=_bool(description="Популярно ли на закат"),
        indoor_observation=_bool(description="Есть ли закрытая смотровая"),
    ),
    PlaceCategory.CHILDREN_CENTERS: _obj(
        age_from=_int(0, 7, description="Минимальный возраст детей"),
        age_to=_int(7, 16, description="Максимальный возраст детей"),
        birthday_parties=_bool(description="Проводят ли дни рождения"),
        classes=_enum_arr(
            "art",
            "sports",
            "languages",
            "stem",
            description="Направления занятий",
        ),
    ),
    PlaceCategory.PLAYGROUNDS: _obj(
        age_from=_int(0, 5, description="Рекомендуемый минимальный возраст"),
        age_to=_int(5, 14, description="Рекомендуемый максимальный возраст"),
        shaded=_bool(description="Есть ли тень / навес"),
        soft_surface=_bool(description="Мягкое покрытие"),
        toilets_nearby=_bool(description="Туалеты рядом"),
    ),
}


def schema_for(category: PlaceCategory) -> Dict[str, Any]:
    if category in CATEGORY_SCHEMAS:
        return CATEGORY_SCHEMAS[category]
    return _obj(
        notes=_str(description="Свободная заметка о месте"),
        price_level=_int(1, 4, description="Ценовой уровень: 1 — бюджетно, 4 — премиум"),
        has_wifi=_bool(description="Есть ли Wi‑Fi"),
    )
