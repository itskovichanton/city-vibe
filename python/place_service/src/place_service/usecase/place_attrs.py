"""Валидация attrs места по JSON Schema категории."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.libs.entities.place import PlaceCategory
from python.place_service.src.place_service.infra.attrs_validation import validate_attrs
from python.place_service.src.place_service.repo.attr_schema import AttrSchemaRepo
from python.place_service.src.place_service.repo.category import CategoryRepo


class PlaceAttrsValidator(Protocol):
    async def resolve_and_validate(
        self,
        category_code: str,
        attrs: dict[str, Any] | None,
    ) -> dict[str, Any]:
        ...


@bean
class PlaceAttrsValidatorImpl(PlaceAttrsValidator):
    category_repo: CategoryRepo
    attr_schema_repo: AttrSchemaRepo

    async def resolve_and_validate(
        self,
        category_code: str,
        attrs: dict[str, Any] | None,
    ) -> dict[str, Any]:
        try:
            PlaceCategory(category_code)
        except ValueError as e:
            raise CoreException(message=f"Неизвестная категория: {category_code}") from e
        cat = await self.category_repo.get_by_code(category_code)
        if cat is None:
            raise CoreException(message=f"Категория {category_code} не найдена в справочнике")
        schema = await self.attr_schema_repo.get_by_category(category_code)
        if schema is None:
            raise CoreException(message=f"JSON Schema для категории {category_code} не найдена")
        return validate_attrs(attrs, schema.json_schema)
