"""
Подбор строк справочника по вольному тексту — без LLM.

Скоринг: подстрока / токен / лёгкий стем / нечёткое совпадение токена
по полям строки и по catalog_aliases.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Iterable, List, Sequence

_WORD_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)
_SUFFIXES = (
    "иями",
    "ями",
    "ами",
    "ого",
    "его",
    "ому",
    "ему",
    "ыми",
    "ими",
    "ое",
    "ее",
    "ая",
    "яя",
    "ие",
    "ые",
    "ой",
    "ий",
    "ый",
    "ом",
    "ем",
    "ах",
    "ях",
    "ам",
    "ям",
    "ов",
    "ев",
    "ую",
    "юю",
    "ей",
    "ий",
    "ть",
)
_STOP = {
    "и",
    "в",
    "на",
    "по",
    "с",
    "со",
    "к",
    "ко",
    "у",
    "о",
    "от",
    "для",
    "как",
    "что",
    "это",
    "или",
    "но",
    "а",
    "же",
    "бы",
    "то",
    "не",
    "ни",
    "да",
    "нет",
    "мне",
    "меня",
    "мой",
    "моя",
    "мои",
    "хочу",
    "хотел",
    "хотела",
    "люблю",
    "любит",
    "потом",
    "после",
    "очень",
    "можно",
    "нужно",
    "где",
    "там",
    "тут",
    "еще",
    "ещё",
    "просто",
    "сегодня",
    "завтра",
    "вечером",
    "утром",
}


@dataclass(frozen=True)
class CatalogAlias:
    catalog: str
    target_code: str
    alias: str
    why: str
    weight: float = 1.0


@dataclass
class CatalogHit:
    key: str
    score: float
    reasons: List[str] = field(default_factory=list)


def normalize(text: str) -> str:
    return (text or "").lower().replace("ё", "е").strip()


def tokenize(text: str) -> List[str]:
    return [normalize(m.group(0)) for m in _WORD_RE.finditer(text or "")]


def stem_ru(token: str) -> str:
    t = normalize(token)
    for reflex in ("ться", "тся"):
        if t.endswith(reflex) and len(t) - len(reflex) >= 4:
            t = t[: -len(reflex)]
            break
    else:
        if len(t) >= 6 and t.endswith(("ся", "сь")):
            t = t[:-2]
    if len(t) < 5:
        return t
    for suf in _SUFFIXES:
        if t.endswith(suf) and len(t) - len(suf) >= 4:
            return t[: -len(suf)]
    return t


def _variant_stems(token: str) -> set[str]:
    """Разговорные корни: фоткаться / фотки ↔ фотосессия."""
    stem = stem_ru(token)
    out = {normalize(token), stem}
    if stem.startswith("фотк") or stem.startswith("фото"):
        out.add("фото")
    return {s for s in out if len(s) >= 2}


def _fuzzy(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _alias_in_prompt(alias: str, prompt_norm: str, tokens: Sequence[str]) -> bool:
    a = normalize(alias)
    if len(a) < 2:
        return False
    if len(a) <= 3:
        stems = {stem_ru(t) for t in tokens}
        return a in tokens or stem_ru(a) in stems
    if a in prompt_norm:
        return True
    a_stem = stem_ru(a)
    a_vars = _variant_stems(a)
    for t in tokens:
        if a in t or t in a:
            return True
        t_stem = stem_ru(t)
        if len(t) >= 4 and (a_stem == t_stem or a_stem in t or t in a_stem):
            return True
        if a_vars & _variant_stems(t):
            return True
        if len(t) >= 5 and len(a) >= 5 and _fuzzy(a, t) >= 0.84:
            return True
    return False


def _field_in_prompt(value: str, prompt_norm: str, tokens: Sequence[str]) -> bool:
    v = normalize(value)
    if len(v) < 2:
        return False
    return _alias_in_prompt(v, prompt_norm, tokens)


def match_catalog_rows(
    prompt: str,
    rows: Iterable[dict],
    aliases: Iterable[CatalogAlias],
    *,
    key_field: str,
    fields: Sequence[str],
    limit: int = 8,
) -> List[tuple[dict, CatalogHit]]:
    """Вернуть строки, отсортированные по score, с why."""
    prompt_norm = normalize(prompt)
    tokens = [t for t in tokenize(prompt) if t not in _STOP and len(t) >= 2]
    if not prompt_norm:
        return []

    by_key: dict[str, CatalogHit] = {}
    row_by_key: dict[str, dict] = {}
    for row in rows:
        key = str(row.get(key_field) or "").strip()
        if not key:
            continue
        row_by_key[key] = row
        by_key[key] = CatalogHit(key=key, score=0.0, reasons=[])

    for alias in aliases:
        key = alias.target_code
        hit = by_key.get(key)
        if hit is None:
            continue
        if not _alias_in_prompt(alias.alias, prompt_norm, tokens):
            continue
        hit.score += 3.0 * float(alias.weight or 1.0)
        reason = (alias.why or "").strip() or f"алиас «{alias.alias}»"
        if reason not in hit.reasons:
            hit.reasons.append(reason)

    for key, row in row_by_key.items():
        hit = by_key[key]
        for field_name in fields:
            raw = row.get(field_name)
            if raw is None:
                continue
            text = str(raw).strip()
            if not text:
                continue
            if not _field_in_prompt(text, prompt_norm, tokens):
                continue
            hit.score += 2.2
            reason = f"поле {field_name} «{text}»"
            if reason not in hit.reasons:
                hit.reasons.append(reason)

    ranked = sorted(
        (h for h in by_key.values() if h.score > 0 and h.reasons),
        key=lambda h: (-h.score, h.key),
    )
    out: List[tuple[dict, CatalogHit]] = []
    for hit in ranked[: max(1, limit)]:
        out.append((row_by_key[hit.key], hit))
    return out


def format_why(hit: CatalogHit) -> str:
    return "; ".join(hit.reasons)
