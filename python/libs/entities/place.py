"""Места, категории, схемы attrs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional

from python.libs.entities.common import Album, Contact, Entity, HasAttrs, Rating
from python.libs.entities.geo import GeoLocation
from python.libs.entities.schedule import WeeklySchedule


class PlaceCategory(StrEnum):
    """Коды категорий мест (seed → place_categories). Источник истины title — в БД."""

    # --- original ---
    BARS = "bars"
    RESTAURANTS = "restaurants"
    CAFES = "cafes"
    HOOKAH = "hookah"
    CONCERTS = "concerts"
    THEATERS = "theaters"
    PARKS = "parks"
    EXHIBITIONS = "exhibitions"
    SPORTS = "sports"
    SHOPPING = "shopping"
    CINEMA = "cinema"
    NIGHTCLUBS = "nightclubs"
    # --- +50 ---
    GYMS = "gyms"
    SWIMMING_POOLS = "swimming_pools"
    QUESTS = "quests"
    BOWLING = "bowling"
    KARAOKE = "karaoke"
    BILLIARDS = "billiards"
    SPA = "spa"
    BEAUTY_SALONS = "beauty_salons"
    BARBERSHOPS = "barbershops"
    MUSEUMS = "museums"
    LIBRARIES = "libraries"
    COWORKING = "coworking"
    BAKERIES = "bakeries"
    STREET_FOOD = "street_food"
    SUSHI = "sushi"
    PIZZA = "pizza"
    BURGERS = "burgers"
    DESSERT_CAFES = "dessert_cafes"
    WINE_BARS = "wine_bars"
    BREWPUBS = "brewpubs"
    LOUNGES = "lounges"
    ROOFTOP_BARS = "rooftop_bars"
    PAINTBALL = "paintball"
    KARTING = "karting"
    SKATING_RINKS = "skating_rinks"
    CLIMBING = "climbing"
    YOGA = "yoga"
    DANCE_STUDIOS = "dance_studios"
    JAZZ_CLUBS = "jazz_clubs"
    COMEDY_CLUBS = "comedy_clubs"
    BOOKSTORES = "bookstores"
    BOARD_GAME_CAFES = "board_game_cafes"
    PET_CAFES = "pet_cafes"
    VR_ARENAS = "vr_arenas"
    LASER_TAG = "laser_tag"
    AQUAPARKS = "aquaparks"
    ZOOS = "zoos"
    PLANETARIUMS = "planetariums"
    PHOTO_STUDIOS = "photo_studios"
    WORKSHOPS = "workshops"
    POTTERY = "pottery"
    ART_GALLERIES = "art_galleries"
    FLOWER_SHOPS = "flower_shops"
    ANTIQUE = "antique"
    FLEA_MARKETS = "flea_markets"
    FARMERS_MARKETS = "farmers_markets"
    MUSIC_SCHOOLS = "music_schools"
    ESCAPE_ROOMS = "escape_rooms"
    MINI_GOLF = "mini_golf"
    SAUNAS = "saunas"
    BANYA = "banya"
    HOOKAH_LOUNGES = "hookah_lounges"
    TEAHOUSES = "teahouses"
    COFFEE_ROASTERS = "coffee_roasters"
    FOOD_TRUCKS = "food_trucks"
    MARKETS = "markets"
    MALLS = "malls"
    WATERFRONTS = "waterfronts"
    VIEWPOINTS = "viewpoints"
    CHILDREN_CENTERS = "children_centers"
    PLAYGROUNDS = "playgrounds"


PLACE_CATEGORY_TITLES: Dict[PlaceCategory, str] = {
    PlaceCategory.BARS: "Бары",
    PlaceCategory.RESTAURANTS: "Рестораны",
    PlaceCategory.CAFES: "Кафе",
    PlaceCategory.HOOKAH: "Кальянные",
    PlaceCategory.CONCERTS: "Концерты",
    PlaceCategory.THEATERS: "Театры",
    PlaceCategory.PARKS: "Парки",
    PlaceCategory.EXHIBITIONS: "Выставки",
    PlaceCategory.SPORTS: "Спорт",
    PlaceCategory.SHOPPING: "Шопинг",
    PlaceCategory.CINEMA: "Кино",
    PlaceCategory.NIGHTCLUBS: "Ночные клубы",
    PlaceCategory.GYMS: "Спортзалы",
    PlaceCategory.SWIMMING_POOLS: "Бассейны",
    PlaceCategory.QUESTS: "Квесты",
    PlaceCategory.BOWLING: "Боулинг",
    PlaceCategory.KARAOKE: "Караоке",
    PlaceCategory.BILLIARDS: "Бильярд",
    PlaceCategory.SPA: "SPA",
    PlaceCategory.BEAUTY_SALONS: "Салоны красоты",
    PlaceCategory.BARBERSHOPS: "Барбершопы",
    PlaceCategory.MUSEUMS: "Музеи",
    PlaceCategory.LIBRARIES: "Библиотеки",
    PlaceCategory.COWORKING: "Коворкинги",
    PlaceCategory.BAKERIES: "Пекарни",
    PlaceCategory.STREET_FOOD: "Стритфуд",
    PlaceCategory.SUSHI: "Суши",
    PlaceCategory.PIZZA: "Пицца",
    PlaceCategory.BURGERS: "Бургеры",
    PlaceCategory.DESSERT_CAFES: "Десерт-кафе",
    PlaceCategory.WINE_BARS: "Винные бары",
    PlaceCategory.BREWPUBS: "Крафт-пабы",
    PlaceCategory.LOUNGES: "Лаунжи",
    PlaceCategory.ROOFTOP_BARS: "Руфтоп-бары",
    PlaceCategory.PAINTBALL: "Пейнтбол",
    PlaceCategory.KARTING: "Картинг",
    PlaceCategory.SKATING_RINKS: "Катки",
    PlaceCategory.CLIMBING: "Скалодромы",
    PlaceCategory.YOGA: "Йога",
    PlaceCategory.DANCE_STUDIOS: "Танцстудии",
    PlaceCategory.JAZZ_CLUBS: "Джаз-клубы",
    PlaceCategory.COMEDY_CLUBS: "Comedy-клубы",
    PlaceCategory.BOOKSTORES: "Книжные",
    PlaceCategory.BOARD_GAME_CAFES: "Настольные кафе",
    PlaceCategory.PET_CAFES: "Антикафе с животными",
    PlaceCategory.VR_ARENAS: "VR-арены",
    PlaceCategory.LASER_TAG: "Лазертаг",
    PlaceCategory.AQUAPARKS: "Аквапарки",
    PlaceCategory.ZOOS: "Зоопарки",
    PlaceCategory.PLANETARIUMS: "Планетарии",
    PlaceCategory.PHOTO_STUDIOS: "Фотостудии",
    PlaceCategory.WORKSHOPS: "Мастерские",
    PlaceCategory.POTTERY: "Гончарные",
    PlaceCategory.ART_GALLERIES: "Галереи",
    PlaceCategory.FLOWER_SHOPS: "Цветочные",
    PlaceCategory.ANTIQUE: "Антиквариат",
    PlaceCategory.FLEA_MARKETS: "Блошиные рынки",
    PlaceCategory.FARMERS_MARKETS: "Фермерские рынки",
    PlaceCategory.MUSIC_SCHOOLS: "Музыкальные школы",
    PlaceCategory.ESCAPE_ROOMS: "Эскейп-румы",
    PlaceCategory.MINI_GOLF: "Мини-гольф",
    PlaceCategory.SAUNAS: "Сауны",
    PlaceCategory.BANYA: "Бани",
    PlaceCategory.HOOKAH_LOUNGES: "Кальян-лаунжи",
    PlaceCategory.TEAHOUSES: "Чайные",
    PlaceCategory.COFFEE_ROASTERS: "Кофейни-обжарщики",
    PlaceCategory.FOOD_TRUCKS: "Фудтраки",
    PlaceCategory.MARKETS: "Рынки",
    PlaceCategory.MALLS: "ТРЦ",
    PlaceCategory.WATERFRONTS: "Набережные",
    PlaceCategory.VIEWPOINTS: "Смотровые",
    PlaceCategory.CHILDREN_CENTERS: "Детские центры",
    PlaceCategory.PLAYGROUNDS: "Площадки",
}

PLACE_CATEGORY_TITLES_EN: Dict[PlaceCategory, str] = {
    PlaceCategory.BARS: "Bars",
    PlaceCategory.RESTAURANTS: "Restaurants",
    PlaceCategory.CAFES: "Cafes",
    PlaceCategory.HOOKAH: "Hookah",
    PlaceCategory.CONCERTS: "Concerts",
    PlaceCategory.THEATERS: "Theaters",
    PlaceCategory.PARKS: "Parks",
    PlaceCategory.EXHIBITIONS: "Exhibitions",
    PlaceCategory.SPORTS: "Sports",
    PlaceCategory.SHOPPING: "Shopping",
    PlaceCategory.CINEMA: "Cinema",
    PlaceCategory.NIGHTCLUBS: "Nightclubs",
    PlaceCategory.GYMS: "Gyms",
    PlaceCategory.SWIMMING_POOLS: "Swimming pools",
    PlaceCategory.QUESTS: "Quests",
    PlaceCategory.BOWLING: "Bowling",
    PlaceCategory.KARAOKE: "Karaoke",
    PlaceCategory.BILLIARDS: "Billiards",
    PlaceCategory.SPA: "SPA",
    PlaceCategory.BEAUTY_SALONS: "Beauty salons",
    PlaceCategory.BARBERSHOPS: "Barbershops",
    PlaceCategory.MUSEUMS: "Museums",
    PlaceCategory.LIBRARIES: "Libraries",
    PlaceCategory.COWORKING: "Coworking",
    PlaceCategory.BAKERIES: "Bakeries",
    PlaceCategory.STREET_FOOD: "Street food",
    PlaceCategory.SUSHI: "Sushi",
    PlaceCategory.PIZZA: "Pizza",
    PlaceCategory.BURGERS: "Burgers",
    PlaceCategory.DESSERT_CAFES: "Dessert cafes",
    PlaceCategory.WINE_BARS: "Wine bars",
    PlaceCategory.BREWPUBS: "Brewpubs",
    PlaceCategory.LOUNGES: "Lounges",
    PlaceCategory.ROOFTOP_BARS: "Rooftop bars",
    PlaceCategory.PAINTBALL: "Paintball",
    PlaceCategory.KARTING: "Karting",
    PlaceCategory.SKATING_RINKS: "Skating rinks",
    PlaceCategory.CLIMBING: "Climbing",
    PlaceCategory.YOGA: "Yoga",
    PlaceCategory.DANCE_STUDIOS: "Dance studios",
    PlaceCategory.JAZZ_CLUBS: "Jazz clubs",
    PlaceCategory.COMEDY_CLUBS: "Comedy clubs",
    PlaceCategory.BOOKSTORES: "Bookstores",
    PlaceCategory.BOARD_GAME_CAFES: "Board game cafes",
    PlaceCategory.PET_CAFES: "Pet cafes",
    PlaceCategory.VR_ARENAS: "VR arenas",
    PlaceCategory.LASER_TAG: "Laser tag",
    PlaceCategory.AQUAPARKS: "Aquaparks",
    PlaceCategory.ZOOS: "Zoos",
    PlaceCategory.PLANETARIUMS: "Planetariums",
    PlaceCategory.PHOTO_STUDIOS: "Photo studios",
    PlaceCategory.WORKSHOPS: "Workshops",
    PlaceCategory.POTTERY: "Pottery",
    PlaceCategory.ART_GALLERIES: "Art galleries",
    PlaceCategory.FLOWER_SHOPS: "Flower shops",
    PlaceCategory.ANTIQUE: "Antique",
    PlaceCategory.FLEA_MARKETS: "Flea markets",
    PlaceCategory.FARMERS_MARKETS: "Farmers markets",
    PlaceCategory.MUSIC_SCHOOLS: "Music schools",
    PlaceCategory.ESCAPE_ROOMS: "Escape rooms",
    PlaceCategory.MINI_GOLF: "Mini golf",
    PlaceCategory.SAUNAS: "Saunas",
    PlaceCategory.BANYA: "Banya",
    PlaceCategory.HOOKAH_LOUNGES: "Hookah lounges",
    PlaceCategory.TEAHOUSES: "Teahouses",
    PlaceCategory.COFFEE_ROASTERS: "Coffee roasters",
    PlaceCategory.FOOD_TRUCKS: "Food trucks",
    PlaceCategory.MARKETS: "Markets",
    PlaceCategory.MALLS: "Malls",
    PlaceCategory.WATERFRONTS: "Waterfronts",
    PlaceCategory.VIEWPOINTS: "Viewpoints",
    PlaceCategory.CHILDREN_CENTERS: "Children centers",
    PlaceCategory.PLAYGROUNDS: "Playgrounds",
}


@dataclass
class PlaceCategoryInfo(Entity):
    """Строка справочника place_categories."""

    code: str
    title: str
    title_en: str = ""
    icon_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


@dataclass
class AttrSchema(Entity):
    """JSON Schema кастомных attrs для категории (1:1 с place_categories)."""

    category_code: str
    json_schema: Dict[str, Any]
    version: int = 1


@dataclass
class Place(Entity, HasAttrs):
    """Место на карте (ресторан, бар, зал и т.д.)."""

    geo: GeoLocation
    name: str
    about: str
    category: PlaceCategory
    owner_id: int
    rating: Optional[Rating] = None
    album: Optional[Album] = None
    contacts: List[Contact] = field(default_factory=list)
    attrs: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[WeeklySchedule] = None
    pin_style_id: Optional[int] = None
    chat_theme_id: Optional[int] = None
    city_id: Optional[int] = None
