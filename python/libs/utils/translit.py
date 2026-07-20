"""Транслитерация кириллицы → латиница (для slug и пр.)."""

from __future__ import annotations

import re
import unicodedata

# Карта транслита (рус → лат). Использовать через transliterate() / slugify().
TRANSLIT_MAP: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def transliterate(text: str) -> str:
    """Транслитерация строки (сохраняет пробелы и прочие символы как есть, кроме кириллицы)."""
    out: list[str] = []
    for ch in text:
        lower = ch.lower()
        if lower in TRANSLIT_MAP:
            mapped = TRANSLIT_MAP[lower]
            out.append(mapped.upper() if ch.isupper() else mapped)
        else:
            out.append(ch)
    return "".join(out)


def slugify(name: str, *, default: str = "item") -> str:
    """URL-slug: кириллица → латиница, пробелы → `-`, только [a-z0-9-]."""
    text = name.strip().lower()
    chars: list[str] = []
    for ch in text:
        if ch in TRANSLIT_MAP:
            chars.append(TRANSLIT_MAP[ch])
        elif "a" <= ch <= "z" or "0" <= ch <= "9":
            chars.append(ch)
        elif ch in {" ", "-", "_"}:
            chars.append("-")
        else:
            norm = unicodedata.normalize("NFKD", ch)
            if norm and norm[0].isascii() and norm[0].isalnum():
                chars.append(norm[0].lower())
    slug = re.sub(r"-+", "-", "".join(chars)).strip("-")
    return slug or default
