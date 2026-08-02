"""Use-cases: стили пинов карты."""

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)

from python.design_service.src.design_service.infra.orm.mappers import pin_to_api
from python.design_service.src.design_service.repo.pin_style import PinStyleRepo


class ListPinStylesUseCase(Protocol):
    async def execute(self) -> list[dict[str, Any]]:
        ...


class GetDefaultPinStyleUseCase(Protocol):
    async def execute(self) -> dict[str, Any]:
        ...


class GetPinStyleUseCase(Protocol):
    async def execute(self, style_id: int) -> dict[str, Any]:
        ...


@bean
class ListPinStylesUseCaseImpl(ListPinStylesUseCase):
    pin_style_repo: PinStyleRepo

    async def execute(self) -> list[dict[str, Any]]:
        pins = await self.pin_style_repo.list_all()
        return [pin_to_api(p) for p in pins]


@bean
class GetDefaultPinStyleUseCaseImpl(GetDefaultPinStyleUseCase):
    pin_style_repo: PinStyleRepo

    async def execute(self) -> dict[str, Any]:
        pin = await self.pin_style_repo.get_by_code("default")
        if pin is None:
            raise CoreException(
                message="default pin style не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return pin_to_api(pin)


@bean
class GetPinStyleUseCaseImpl(GetPinStyleUseCase):
    pin_style_repo: PinStyleRepo

    async def execute(self, style_id: int) -> dict[str, Any]:
        pin = await self.pin_style_repo.get_by_id(style_id)
        if pin is None:
            raise CoreException(
                message=f"Pin style id={style_id} не найден",
                reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
            )
        return pin_to_api(pin)
