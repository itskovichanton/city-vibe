"""
ООП-операции фильтрации Place.attrs.

Контракт значения в запросе:
  - скаляр / bool / number / string / array  → ExactMatch
  - {"operation": "between", "args": {"from"?: n, "to"?: n}}
  - {"operation": "or", "args": {"list": [...]}}
  - {"operation": "and", "args": {"list": [...]}}
  - {"operation": "not_in", "args": {"list": [...]}}

Вложенности операций нет — одна операция на поле.
Новые операции добавляются регистрацией в ATTR_OP_REGISTRY.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type

from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException


SqlFragment = Tuple[str, Dict[str, Any]]  # (sql with :named params, params dict)


class AttrOperation(ABC):
    """Базовая операция фильтра по одному ключу attrs."""

    name: ClassVar[str]

    @abstractmethod
    def to_sql(self, key: str, param_prefix: str) -> SqlFragment:
        """
        SQL-условие относительно колонки places.attrs.
        param_prefix — уникальный префикс имён bind-параметров.
        """

    @classmethod
    @abstractmethod
    def from_args(cls, args: Dict[str, Any]) -> "AttrOperation":
        ...


@dataclass(frozen=True)
class ExactMatch(AttrOperation):
    """Точное совпадение JSON-значения (bool/number/string/array/object)."""

    name: ClassVar[str] = "exact"
    value: Any

    def to_sql(self, key: str, param_prefix: str) -> SqlFragment:
        import json

        p = f"{param_prefix}_exact"
        return (
            f"attrs @> CAST(:{p} AS jsonb)",
            {p: json.dumps({key: self.value}, ensure_ascii=False)},
        )

    @classmethod
    def from_args(cls, args: Dict[str, Any]) -> "ExactMatch":
        if "value" not in args:
            raise CoreException(message="exact: нужен args.value")
        return cls(value=args["value"])


@dataclass(frozen=True)
class BetweenOp(AttrOperation):
    """Числовой диапазон: from/to опциональны (открытые границы)."""

    name: ClassVar[str] = "between"
    from_value: Optional[float] = None
    to_value: Optional[float] = None

    def to_sql(self, key: str, param_prefix: str) -> SqlFragment:
        if self.from_value is None and self.to_value is None:
            raise CoreException(message="between: укажите args.from и/или args.to")
        parts: List[str] = []
        params: Dict[str, Any] = {}
        # NULL attrs не проходят
        expr = f"(attrs->>'{key}')::numeric"
        parts.append(f"attrs ? '{key}'")
        if self.from_value is not None:
            p = f"{param_prefix}_from"
            parts.append(f"{expr} >= :{p}")
            params[p] = self.from_value
        if self.to_value is not None:
            p = f"{param_prefix}_to"
            parts.append(f"{expr} <= :{p}")
            params[p] = self.to_value
        return ("(" + " AND ".join(parts) + ")", params)

    @classmethod
    def from_args(cls, args: Dict[str, Any]) -> "BetweenOp":
        return cls(
            from_value=args.get("from", args.get("from_")),
            to_value=args.get("to"),
        )


@dataclass(frozen=True)
class OrOp(AttrOperation):
    """
    ИЛИ по списку значений.
    - если в attrs значение — scalar: attrs[key] IN list
    - если array: пересечение (есть хотя бы один общий элемент)
    Реализуем универсально: scalar → IN; array → ?| (есть ключ-элемент) / overlap.
    Используем: (jsonb_typeof = 'array' AND overlap) OR (scalar IN list).
    """

    name: ClassVar[str] = "or"
    values: Tuple[Any, ...]

    def to_sql(self, key: str, param_prefix: str) -> SqlFragment:
        if not self.values:
            raise CoreException(message="or: args.list не должен быть пустым")
        p_arr = f"{param_prefix}_or_arr"
        p_scalars = f"{param_prefix}_or_sc"
        # array overlap via ?| needs text[]; also handle scalar membership
        sql = (
            f"("
            f"(jsonb_typeof(attrs->'{key}') = 'array' AND attrs->'{key}' ?| CAST(:{p_arr} AS text[])) "
            f"OR (jsonb_typeof(attrs->'{key}') <> 'array' AND attrs->>'{key}' = ANY(CAST(:{p_scalars} AS text[])))"
            f")"
        )
        as_text = [str(v) if not isinstance(v, bool) else ("true" if v else "false") for v in self.values]
        # for bool/number stored as json, ->> gives text representation
        return (sql, {p_arr: as_text, p_scalars: as_text})

    @classmethod
    def from_args(cls, args: Dict[str, Any]) -> "OrOp":
        lst = args.get("list")
        if not isinstance(lst, list):
            raise CoreException(message="or: нужен args.list (array)")
        return cls(values=tuple(lst))


@dataclass(frozen=True)
class AndOp(AttrOperation):
    """
    И по списку значений (для array-атрибутов: все элементы list ⊆ attrs[key]).
    Для scalar — attrs[key] должен равняться единственному значению (list длины 1)
    или входить во все? Обычно and для массивов: containment @>.
    """

    name: ClassVar[str] = "and"
    values: Tuple[Any, ...]

    def to_sql(self, key: str, param_prefix: str) -> SqlFragment:
        import json

        if not self.values:
            raise CoreException(message="and: args.list не должен быть пустым")
        p = f"{param_prefix}_and"
        return (
            f"(jsonb_typeof(attrs->'{key}') = 'array' AND attrs->'{key}' @> CAST(:{p} AS jsonb))",
            {p: json.dumps(list(self.values), ensure_ascii=False)},
        )

    @classmethod
    def from_args(cls, args: Dict[str, Any]) -> "AndOp":
        lst = args.get("list")
        if not isinstance(lst, list):
            raise CoreException(message="and: нужен args.list (array)")
        return cls(values=tuple(lst))


@dataclass(frozen=True)
class NotInOp(AttrOperation):
    """
    Исключение значений из списка (NOT IN).
    - scalar: attrs[key] ∉ list
    - array: нет пересечения с list
    Отсутствующий ключ проходит фильтр (значение не входит в запрещённый список).
    """

    name: ClassVar[str] = "not_in"
    values: Tuple[Any, ...]

    def to_sql(self, key: str, param_prefix: str) -> SqlFragment:
        if not self.values:
            raise CoreException(message="not_in: args.list не должен быть пустым")
        p_arr = f"{param_prefix}_nin_arr"
        p_scalars = f"{param_prefix}_nin_sc"
        # логическое отрицание OrOp: нет overlap у array и scalar не в list
        sql = (
            f"("
            f"attrs->'{key}' IS NULL "
            f"OR ("
            f"jsonb_typeof(attrs->'{key}') = 'array' "
            f"AND NOT (attrs->'{key}' ?| CAST(:{p_arr} AS text[]))"
            f") "
            f"OR ("
            f"jsonb_typeof(attrs->'{key}') <> 'array' "
            f"AND NOT (attrs->>'{key}' = ANY(CAST(:{p_scalars} AS text[])))"
            f")"
            f")"
        )
        as_text = [str(v) if not isinstance(v, bool) else ("true" if v else "false") for v in self.values]
        return (sql, {p_arr: as_text, p_scalars: as_text})

    @classmethod
    def from_args(cls, args: Dict[str, Any]) -> "NotInOp":
        lst = args.get("list")
        if not isinstance(lst, list):
            raise CoreException(message="not_in: нужен args.list (array)")
        return cls(values=tuple(lst))


ATTR_OP_REGISTRY: Dict[str, Type[AttrOperation]] = {
    ExactMatch.name: ExactMatch,
    BetweenOp.name: BetweenOp,
    OrOp.name: OrOp,
    AndOp.name: AndOp,
    NotInOp.name: NotInOp,
}


def register_attr_operation(cls: Type[AttrOperation]) -> Type[AttrOperation]:
    """Декоратор для расширения набора операций."""
    ATTR_OP_REGISTRY[cls.name] = cls
    return cls


def parse_attr_predicate(key: str, raw: Any) -> AttrOperation:
    """Преобразует значение из тела запроса в операцию."""
    if isinstance(raw, dict) and "operation" in raw:
        op_name = str(raw["operation"]).lower().strip()
        cls = ATTR_OP_REGISTRY.get(op_name)
        if cls is None:
            known = ", ".join(sorted(ATTR_OP_REGISTRY))
            raise CoreException(message=f"Неизвестная attrs-операция '{op_name}'. Доступны: {known}")
        args = raw.get("args") or {}
        if not isinstance(args, dict):
            raise CoreException(message=f"{op_name}: args должен быть объектом")
        # запрет вложенных операций
        for v in args.values():
            if isinstance(v, dict) and "operation" in v:
                raise CoreException(message="Вложенные операции в attrs не поддерживаются")
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and "operation" in item:
                        raise CoreException(message="Вложенные операции в attrs не поддерживаются")
        return cls.from_args(args)
    return ExactMatch(value=raw)


def compile_attrs_filters(attrs: Dict[str, Any]) -> SqlFragment:
    """Собирает AND по всем ключам attrs-фильтра."""
    if not attrs:
        return ("TRUE", {})
    clauses: List[str] = []
    params: Dict[str, Any] = {}
    for i, (key, raw) in enumerate(attrs.items()):
        if not isinstance(key, str) or not key:
            raise CoreException(message="Ключи attrs должны быть непустыми строками")
        # защита от инъекций в ключ
        if not key.replace("_", "").isalnum():
            raise CoreException(message=f"Недопустимый ключ attrs: {key}")
        op = parse_attr_predicate(key, raw)
        sql, p = op.to_sql(key, f"a{i}")
        clauses.append(sql)
        # sqlalchemy text() с :name — для jsonb dict нужен json.dumps позже в repo
        params.update(p)
    return ("(" + " AND ".join(clauses) + ")", params)
