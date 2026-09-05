"""Use-cases: CRUD продуктов."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.libs.entities.place import ProductCategory
from python.place_service.src.place_service.entities.common import (
    CreateProductRequest,
    DeleteProductRequest,
    DeleteProductResponse,
    ListProductsRequest,
    PatchProductRequest,
)
from python.place_service.src.place_service.infra.orm.mappers import (
    compact_place_dict,
    product_to_api_dict,
)
from python.place_service.src.place_service.repo.place import PlaceRepo
from python.place_service.src.place_service.repo.product import ProductRepo
from python.place_service.src.place_service.repo.product_category import ProductCategoryRepo


def _validate_category_code(code: str) -> None:
    try:
        ProductCategory(code)
    except ValueError as e:
        raise CoreException(message=f"Неизвестная категория продукта: {code}") from e


class CreateProductUseCase(Protocol):
    async def execute(self, request: CreateProductRequest) -> dict[str, Any]:
        ...


class ListProductsUseCase(Protocol):
    async def execute(self, request: ListProductsRequest) -> list[dict[str, Any]]:
        ...


class GetProductUseCase(Protocol):
    async def execute(self, product_id: int) -> dict[str, Any]:
        ...


class PatchProductUseCase(Protocol):
    async def execute(self, request: PatchProductRequest) -> dict[str, Any]:
        ...


class DeleteProductUseCase(Protocol):
    async def execute(self, request: DeleteProductRequest) -> DeleteProductResponse:
        ...


@bean
class CreateProductUseCaseImpl(CreateProductUseCase):
    product_repo: ProductRepo
    product_category_repo: ProductCategoryRepo
    place_repo: PlaceRepo

    async def execute(self, request: CreateProductRequest) -> dict[str, Any]:
        _validate_category_code(request.category)
        cat = await self.product_category_repo.get_by_code(request.category)
        if cat is None:
            raise CoreException(message=f"Категория продукта {request.category} не найдена")
        place = await self.place_repo.get_by_id(request.place_id)
        if place is None:
            raise CoreException(
                message=f"Место id={request.place_id} не найдено",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        product = await self.product_repo.create(
            place_id=request.place_id,
            name=request.name,
            description=request.description,
            price=request.price,
            category_code=request.category,
            schedule=request.schedule,
        )
        return product_to_api_dict(product, place=compact_place_dict(place))


@bean
class ListProductsUseCaseImpl(ListProductsUseCase):
    product_repo: ProductRepo
    place_repo: PlaceRepo

    async def execute(self, request: ListProductsRequest) -> list[dict[str, Any]]:
        products = await self.product_repo.list(
            place_id=request.place_id,
            category=request.category,
            limit=request.limit,
        )
        out: list[dict[str, Any]] = []
        for product in products:
            place = await self.place_repo.get_by_id(product.place_id)
            out.append(
                product_to_api_dict(
                    product,
                    place=compact_place_dict(place) if place else None,
                )
            )
        return out


@bean
class GetProductUseCaseImpl(GetProductUseCase):
    product_repo: ProductRepo
    place_repo: PlaceRepo

    async def execute(self, product_id: int) -> dict[str, Any]:
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            raise CoreException(
                message=f"Продукт id={product_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        place = await self.place_repo.get_by_id(product.place_id)
        return product_to_api_dict(
            product,
            place=compact_place_dict(place) if place else None,
        )


@bean
class PatchProductUseCaseImpl(PatchProductUseCase):
    product_repo: ProductRepo
    product_category_repo: ProductCategoryRepo
    place_repo: PlaceRepo

    async def execute(self, request: PatchProductRequest) -> dict[str, Any]:
        existing = await self.product_repo.get_by_id(request.product_id)
        if existing is None:
            raise CoreException(
                message=f"Продукт id={request.product_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if "price" in request.fields_set:
            updates["price"] = request.price
        if request.category is not None:
            _validate_category_code(request.category)
            cat = await self.product_category_repo.get_by_code(request.category)
            if cat is None:
                raise CoreException(message=f"Категория продукта {request.category} не найдена")
            updates["category_code"] = request.category
        if "schedule" in request.fields_set:
            updates["schedule"] = request.schedule
        product = await self.product_repo.update(request.product_id, **updates)
        place = await self.place_repo.get_by_id(product.place_id)
        return product_to_api_dict(
            product,
            place=compact_place_dict(place) if place else None,
        )


@bean
class DeleteProductUseCaseImpl(DeleteProductUseCase):
    product_repo: ProductRepo

    async def execute(self, request: DeleteProductRequest) -> DeleteProductResponse:
        ok = await self.product_repo.soft_delete(request.product_id)
        if not ok:
            raise CoreException(
                message=f"Продукт id={request.product_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return DeleteProductResponse(ok=True, product_id=request.product_id)
