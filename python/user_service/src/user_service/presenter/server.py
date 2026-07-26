"""HTTP-сервер FastAPI: Swagger UI, OpenAPI, async-эндпоинты + infra decorators."""

from datetime import date
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from pydantic import BaseModel, Field
from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.error_handler import ErrorHandlerFastAPISupport
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.exceptions import (
    ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
    CoreException,
)
from src.mybootstrap_mvc_itskovichanton.pipeline import ActionRunner, Result
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from python.libs.clients.infra.s3 import FileStorage
from python.libs.entities.place import PlaceCategory
from python.libs.entities.user import Gender
from python.libs.infra import CityVibeInfraSupport
from python.libs.infra.decorators import idempotent, rate_limit, read_validated_upload, require_s2s
from python.user_service.src.user_service.entities.common import (
    CompleteOnboardingRequest,
    CreateUserRequest,
    UpdateBioRequest,
)
from python.user_service.src.user_service.repo.user import UserRepo
from python.user_service.src.user_service.usecase.complete_onboarding import CompleteOnboardingUseCase
from python.user_service.src.user_service.usecase.create_user import CreateUserUseCase
from python.user_service.src.user_service.usecase.get_user import GetUserUseCase
from python.user_service.src.user_service.usecase.update_bio import UpdateBioUseCase


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


@bean(port=("server.port", int, 8081), host=("server.host", str, "0.0.0.0"))
class Server:
    """FastAPI-сервер user-service."""

    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    infra_support: CityVibeInfraSupport
    action_runner: ActionRunner
    create_user_uc: CreateUserUseCase
    update_bio_uc: UpdateBioUseCase
    complete_onboarding_uc: CompleteOnboardingUseCase
    get_user_uc: GetUserUseCase
    file_storage: FileStorage
    user_repo: UserRepo
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
        # Request-ID / S2S / Idempotency middleware — по ENV-флагам
        self.infra_support.mount(app)
        return app

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            return self.presenter.present(
                Result(result={"status": "ok", "service": "user-service"}),
            )

        @self.fast_api.post("/users", tags=["users"], summary="Создать пользователя (онбординг, шаг 1)")
        @require_s2s
        @idempotent("users.create")
        @rate_limit("users.create", limit=30)
        async def create_user(request: Request, body: CreateUserBody):
            categories: list[PlaceCategory] = []
            for code in body.favorite_categories:
                try:
                    categories.append(PlaceCategory(code))
                except ValueError:
                    continue
            req = CreateUserRequest(
                name=body.name,
                gender=body.gender,
                age=body.age,
                short_bio=body.short_bio,
                favorite_categories=categories,
                city_id=body.city_id,
                birthdate=body.birthdate,
                auth_account_id=body.auth_account_id,
            )
            return self.presenter.present(
                await self.action_runner.run(self.create_user_uc.execute, call=req),
            )

        @self.fast_api.get("/users/{user_id}", tags=["users"], summary="Получить профиль")
        @require_s2s
        @rate_limit("users.get", limit=120)
        async def get_user(request: Request, user_id: int):
            return self.presenter.present(
                await self.action_runner.run(self.get_user_uc.execute, call=user_id),
            )

        @self.fast_api.put("/users/{user_id}/bio", tags=["users"], summary="Обновить bio")
        @require_s2s
        @idempotent("users.bio")
        @rate_limit("users.bio", limit=60)
        async def update_bio(request: Request, user_id: int, body: UpdateBioBody):
            req = UpdateBioRequest(user_id=user_id, long_bio=body.long_bio)
            return self.presenter.present(
                await self.action_runner.run(self.update_bio_uc.execute, call=req),
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
            req = CompleteOnboardingRequest(user_id=user_id)
            return self.presenter.present(
                await self.action_runner.run(self.complete_onboarding_uc.execute, call=req),
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
            async def _upload(_):
                user = await self.user_repo.get_by_id(user_id)
                if user is None:
                    raise CoreException(
                        message=f"Пользователь id={user_id} не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                data, content_type, ext = await read_validated_upload(file)
                url = await self.file_storage.upload(
                    data,
                    content_type=content_type,
                    key_prefix=f"avatars/{user_id}",
                    extension=ext,
                )
                user.avatar_url = url
                await self.user_repo.save(user)
                return await self.get_user_uc.execute(user_id)

            return self.presenter.present(await self.action_runner.run(_upload, call=None))

        @self.fast_api.delete("/users/{user_id}", tags=["users"], summary="Soft-delete пользователя")
        @require_s2s
        async def delete_user(request: Request, user_id: int):
            async def _delete(_):
                ok = await self.user_repo.soft_delete(user_id)
                if not ok:
                    raise CoreException(
                        message=f"Пользователь id={user_id} не найден",
                        reason=ERR_REASON_SERVER_RESPONDED_WITH_ERROR_NOT_FOUND,
                    )
                return {"ok": True, "user_id": user_id}

            return self.presenter.present(await self.action_runner.run(_delete, call=None))
