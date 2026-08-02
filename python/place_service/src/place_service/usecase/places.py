"""Use-cases: CRUD мест."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.place_service.src.place_service.entities.common import (
    CreatePlaceRequest,
    DeletePlaceRequest,
    DeletePlaceResponse,
    ListPlacesRequest,
    PatchPlaceRequest,
)
from python.place_service.src.place_service.infra.orm.mappers import place_to_api_dict
from python.place_service.src.place_service.repo.place import PlaceRepo
from python.place_service.src.place_service.usecase.place_attrs import PlaceAttrsValidator


class CreatePlaceUseCase(Protocol):
    async def execute(self, request: CreatePlaceRequest) -> dict[str, Any]:
        ...


class ListPlacesUseCase(Protocol):
    async def execute(self, request: ListPlacesRequest) -> list[dict[str, Any]]:
        ...


class GetPlaceUseCase(Protocol):
    async def execute(self, place_id: int) -> dict[str, Any]:
        ...


class PatchPlaceUseCase(Protocol):
    async def execute(self, request: PatchPlaceRequest) -> dict[str, Any]:
        ...


class DeletePlaceUseCase(Protocol):
    async def execute(self, request: DeletePlaceRequest) -> DeletePlaceResponse:
        ...


@bean
class CreatePlaceUseCaseImpl(CreatePlaceUseCase):
    place_repo: PlaceRepo
    place_attrs_validator: PlaceAttrsValidator

    async def execute(self, request: CreatePlaceRequest) -> dict[str, Any]:
        attrs = await self.place_attrs_validator.resolve_and_validate(request.category, request.attrs)
        place = await self.place_repo.create(
            name=request.name,
            about=request.about,
            category_code=request.category,
            owner_id=request.owner_id,
            lat=request.lat,
            lng=request.lng,
            attrs=attrs,
            schedule=request.schedule,
            pin_style_id=request.pin_style_id,
            chat_theme_id=request.chat_theme_id,
            city_id=request.city_id,
            contacts=request.contacts,
        )
        return place_to_api_dict(place)


@bean
class ListPlacesUseCaseImpl(ListPlacesUseCase):
    place_repo: PlaceRepo

    async def execute(self, request: ListPlacesRequest) -> list[dict[str, Any]]:
        places = await self.place_repo.list(
            owner_id=request.owner_id,
            category=request.category,
            bbox=request.bbox,
            limit=request.limit,
        )
        return [place_to_api_dict(p) for p in places]


@bean
class GetPlaceUseCaseImpl(GetPlaceUseCase):
    place_repo: PlaceRepo

    async def execute(self, place_id: int) -> dict[str, Any]:
        place = await self.place_repo.get_by_id(place_id)
        if place is None:
            raise CoreException(
                message=f"Место id={place_id} не найдено",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return place_to_api_dict(place)


@bean
class PatchPlaceUseCaseImpl(PatchPlaceUseCase):
    place_repo: PlaceRepo
    place_attrs_validator: PlaceAttrsValidator

    async def execute(self, request: PatchPlaceRequest) -> dict[str, Any]:
        existing = await self.place_repo.get_by_id(request.place_id)
        if existing is None:
            raise CoreException(
                message=f"Место id={request.place_id} не найдено",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )

        updates: dict[str, Any] = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.about is not None:
            updates["about"] = request.about
        category_code = request.category or existing.category.value
        if request.category is not None:
            updates["category_code"] = request.category
        if request.lat is not None and request.lng is not None:
            updates["lat"] = request.lat
            updates["lng"] = request.lng
        if request.attrs is not None or request.category is not None:
            attrs_src = request.attrs if request.attrs is not None else existing.attrs
            updates["attrs"] = await self.place_attrs_validator.resolve_and_validate(
                category_code,
                attrs_src,
            )
        if request.schedule is not None:
            updates["schedule"] = request.schedule
        if "pin_style_id" in request.fields_set:
            updates["pin_style_id"] = request.pin_style_id
        if "chat_theme_id" in request.fields_set:
            updates["chat_theme_id"] = request.chat_theme_id
        if "city_id" in request.fields_set:
            updates["city_id"] = request.city_id
        if request.contacts is not None:
            updates["contacts"] = request.contacts

        place = await self.place_repo.update(request.place_id, **updates)
        return place_to_api_dict(place)


@bean
class DeletePlaceUseCaseImpl(DeletePlaceUseCase):
    place_repo: PlaceRepo

    async def execute(self, request: DeletePlaceRequest) -> DeletePlaceResponse:
        ok = await self.place_repo.soft_delete(request.place_id)
        if not ok:
            raise CoreException(
                message=f"Место id={request.place_id} не найдено",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return DeletePlaceResponse(ok=True, place_id=request.place_id)
