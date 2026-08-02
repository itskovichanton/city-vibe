"""Use-cases: JSON Schema attrs по категориям."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.libs.utils.schema_compact import compact_json_schema
from python.place_service.src.place_service.entities.common import GetAttrSchemaRequest
from python.place_service.src.place_service.infra.orm.mappers import attr_schema_to_api
from python.place_service.src.place_service.repo.attr_schema import AttrSchemaRepo


class ListAttrSchemasUseCase(Protocol):
    async def execute(self) -> list[dict[str, Any]]:
        ...


class GetAttrSchemaUseCase(Protocol):
    async def execute(self, request: GetAttrSchemaRequest) -> dict[str, Any]:
        ...


@bean
class ListAttrSchemasUseCaseImpl(ListAttrSchemasUseCase):
    attr_schema_repo: AttrSchemaRepo

    async def execute(self) -> list[dict[str, Any]]:
        items = await self.attr_schema_repo.list_all()
        return [
            {
                "id": s.id,
                "category_code": s.category_code,
                "version": s.version,
                "json_schema": s.json_schema,
            }
            for s in items
        ]


@bean
class GetAttrSchemaUseCaseImpl(GetAttrSchemaUseCase):
    attr_schema_repo: AttrSchemaRepo

    async def execute(self, request: GetAttrSchemaRequest) -> dict[str, Any]:
        schema = await self.attr_schema_repo.get_by_category(request.category_code)
        if schema is None:
            raise CoreException(
                message=f"Schema для {request.category_code} не найдена",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        json_schema = schema.json_schema
        if request.compact:
            json_schema = compact_json_schema(json_schema)
        return attr_schema_to_api(schema, compact=request.compact, json_schema=json_schema)
