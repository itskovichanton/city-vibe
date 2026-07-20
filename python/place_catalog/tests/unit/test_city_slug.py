"""Тест slugify / translit из libs.utils."""

from python.libs.utils.translit import slugify, transliterate


def test_slugify_cyrillic():
    assert slugify("Москва") == "moskva"
    assert slugify("Санкт-Петербург") == "sankt-peterburg"


def test_slugify_latin():
    assert slugify("Sochi") == "sochi"


def test_transliterate():
    assert transliterate("Привет") == "Privet"
