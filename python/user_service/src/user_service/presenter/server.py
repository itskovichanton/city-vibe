"""HTTP-сервер FastAPI: Swagger UI, OpenAPI, async-эндпоинты + infra decorators."""

from datetime import date
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.error_handler import ErrorHandlerFastAPISupport
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.pipeline import ActionRunner, Result
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from python.libs.entities.user import Gender
from python.libs.infra import CityVibeInfraSupport
from python.libs.infra.decorators import idempotent, rate_limit, read_validated_upload, require_s2s
from python.user_service.src.user_service.presenter.mappers import (
    to_complete_onboarding_request,
    to_create_user_request,
    to_delete_user_request,
    to_update_bio_request,
    to_update_profile_request,
    to_upload_avatar_request,
)
from python.user_service.src.user_service.usecase.complete_onboarding import CompleteOnboardingUseCase
from python.user_service.src.user_service.usecase.create_user import CreateUserUseCase
from python.user_service.src.user_service.usecase.delete_user import DeleteUserUseCase
from python.user_service.src.user_service.usecase.get_milana_account import GetMilanaAccountUseCase
from python.user_service.src.user_service.usecase.get_media import GetMediaUseCase
from python.user_service.src.user_service.usecase.get_user import GetUserUseCase
from python.user_service.src.user_service.usecase.update_bio import UpdateBioUseCase
from python.user_service.src.user_service.usecase.update_profile import UpdateProfileUseCase
from python.user_service.src.user_service.usecase.upload_avatar import UploadAvatarUseCase


class CreateUserBody(BaseModel):
    name: str = Field(..., description="Имя")
    gender: Gender = Field(..., description="Пол")
    age: Optional[int] = Field(None, description="Возраст 1..120")
    short_bio: str = Field("", description="Коротко о себе")
    favorite_categories: List[str] = Field(default_factory=list, description="Любимые категории мест")
    city_id: Optional[int] = Field(None, description="ID города из place-service")
    birthdate: Optional[date] = Field(None, description="Дата рождения")
    auth_account_id: Optional[int] = Field(None, description="ID аккаунта auth-service")


class UpdateBioBody(BaseModel):
    long_bio: str = Field(..., description="О себе в свободной форме")


class UpdateProfileBody(BaseModel):
    name: Optional[str] = Field(None, description="Имя пользователя")
    favorite_categories: Optional[List[str]] = Field(
        None,
        description="Коды любимых категорий мест (PlaceCategory)",
    )


@bean(port=("server.port", int, 8081), host=("server.host", str, "0.0.0.0"))
class Server:
    """FastAPI-сервер user-service."""

    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    create_user_uc: CreateUserUseCase
    update_bio_uc: UpdateBioUseCase
    update_profile_uc: UpdateProfileUseCase
    complete_onboarding_uc: CompleteOnboardingUseCase
    get_user_uc: GetUserUseCase
    get_milana_account_uc: GetMilanaAccountUseCase
    get_media_uc: GetMediaUseCase
    upload_avatar_uc: UploadAvatarUseCase
    delete_user_uc: DeleteUserUseCase
    logger_service: LoggerService
    presenter: ResultPresenter = default_dataclass_field(
        JSONResultPresenterImpl(exclude_unset=True),
    )

    def init(self, **kwargs):
        self.port = kwargs.get("port", getattr(self, "port", 8081))
        self.host = kwargs.get("host", getattr(self, "host", "0.0.0.0"))
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        app = FastAPI(
            title="City Vibe — User Service",
            description="Профили пользователей и онбординг",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )
        self.error_handler_fast_api_support.mount(app)
        self.infra_support.mount(app)
        return app

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            return self.presenter.present(
                Result(result={"status": "ok", "service": "user-service"}),
            )

        @self.fast_api.get(
            "/media/{path:path}",
            tags=["media"],
            summary="Файл из S3 (аватар и др.)",
            response_class=Response,
        )
        @rate_limit("media.get", limit=300)
        async def get_media(request: Request, path: str):
            presented = await self.action_runner.run(
                self.get_media_uc.execute,
                call=path,
            )
            content = presented.result
            return Response(
                content=content.data,
                media_type=content.content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )

        @self.fast_api.post("/users", tags=["users"], summary="Создать пользователя (онбординг, шаг 1)")
        @require_s2s
        @idempotent("users.create")
        @rate_limit("users.create", limit=30)
        async def create_user(request: Request, body: CreateUserBody):
            return self.presenter.present(
                await self.action_runner.run(
                    self.create_user_uc.execute,
                    call=to_create_user_request(body),
                ),
            )

        @self.fast_api.get("/users/{user_id}", tags=["users"], summary="Получить профиль")
        @require_s2s
        @rate_limit("users.get", limit=120)
        async def get_user(request: Request, user_id: int):
            return self.presenter.present(
                await self.action_runner.run(self.get_user_uc.execute, call=user_id),
            )

        @self.fast_api.get(
            "/users/system/milana",
            tags=["users", "system"],
            summary="Служебный аккаунт Миланы (role=MILANA)",
        )
        @rate_limit("users.milana", limit=120)
        async def get_milana_account(request: Request):
            return self.presenter.present(
                await self.action_runner.run(self.get_milana_account_uc.execute, call=None),
            )

        @self.fast_api.patch("/users/{user_id}", tags=["users"], summary="Обновить профиль")
        @require_s2s
        @idempotent("users.update")
        @rate_limit("users.update", limit=60)
        async def update_profile(request: Request, user_id: int, body: UpdateProfileBody):
            return self.presenter.present(
                await self.action_runner.run(
                    self.update_profile_uc.execute,
                    call=to_update_profile_request(user_id, body),
                ),
            )

        @self.fast_api.put("/users/{user_id}/bio", tags=["users"], summary="Обновить bio")
        @require_s2s
        @idempotent("users.bio")
        @rate_limit("users.bio", limit=60)
        async def update_bio(request: Request, user_id: int, body: UpdateBioBody):
            return self.presenter.present(
                await self.action_runner.run(
                    self.update_bio_uc.execute,
                    call=to_update_bio_request(user_id, body),
                ),
            )

        @self.fast_api.post(
            "/users/{user_id}/onboarding/complete",
            tags=["users"],
            summary="Завершить онбординг",
        )
        @require_s2s
        @idempotent("users.onboarding.complete")
        @rate_limit("users.onboarding", limit=20)
        async def complete_onboarding(request: Request, user_id: int):
            return self.presenter.present(
                await self.action_runner.run(
                    self.complete_onboarding_uc.execute,
                    call=to_complete_onboarding_request(user_id),
                ),
            )

        @self.fast_api.post(
            "/users/{user_id}/avatar",
            tags=["users"],
            summary="Загрузить аватарку в S3",
        )
        @require_s2s
        @idempotent("users.avatar")
        @rate_limit("users.avatar", limit=10, window_sec=60)
        async def upload_avatar(
            request: Request,
            user_id: int,
            file: UploadFile = File(..., description="Файл изображения"),
        ):
            data, content_type, ext = await read_validated_upload(file)
            return self.presenter.present(
                await self.action_runner.run(
                    self.upload_avatar_uc.execute,
                    call=to_upload_avatar_request(
                        user_id,
                        data=data,
                        content_type=content_type,
                        extension=ext,
                    ),
                ),
            )

        @self.fast_api.delete("/users/{user_id}", tags=["users"], summary="Soft-delete пользователя")
        @require_s2s
        async def delete_user(request: Request, user_id: int):
            return self.presenter.present(
                await self.action_runner.run(
                    self.delete_user_uc.execute,
                    call=to_delete_user_request(user_id),
                ),
            )
