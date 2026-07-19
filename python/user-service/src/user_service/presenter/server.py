"""HTTP-сервер FastAPI: Swagger UI, OpenAPI, async-эндпоинты."""

from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, UploadFile
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
from src.mybootstrap_mvc_itskovichanton.pipeline import ActionRunner
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter

from python.libs.clients.infra.s3 import FileStorage
from python.libs.entities.user import PlaceCategory
from user_service.entities.common import (
    CompleteOnboardingRequest,
    CreateUserRequest,
    UpdateBioRequest,
)
from user_service.repo.user import UserRepo
from user_service.usecase.complete_onboarding import CompleteOnboardingUseCase
from user_service.usecase.create_user import CreateUserUseCase
from user_service.usecase.get_user import GetUserUseCase
from user_service.usecase.update_bio import UpdateBioUseCase


class CreateUserBody(BaseModel):
    """Тело запроса создания профиля (шаг 1)."""

    name: str = Field(..., description="Имя")
    age: Optional[int] = Field(None, description="Возраст 1..120")
    short_bio: str = Field("", description="Коротко о себе")
    favorite_categories: List[str] = Field(
        default_factory=list,
        description="Любимые категории мест",
    )


class UpdateBioBody(BaseModel):
    """Тело запроса развёрнутого bio (шаг 2)."""

    long_bio: str = Field(..., description="О себе в свободной форме")


@bean(port=("server.port", int, 8081), host=("server.host", str, "0.0.0.0"))
class Server:
    """FastAPI-сервер user-service."""

    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    action_runner: ActionRunner
    # Use-case инжектятся напрямую (без отдельного controller)
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
        return app

    def add_routes(self):
        @self.fast_api.get("/health", tags=["infra"])
        async def health():
            return {"status": "ok", "service": "user-service"}

        @self.fast_api.post(
            "/users",
            tags=["users"],
            summary="Создать пользователя (онбординг, шаг 1)",
        )
        async def create_user(body: CreateUserBody):
            categories: list[PlaceCategory] = []
            for code in body.favorite_categories:
                try:
                    categories.append(PlaceCategory(code))
                except ValueError:
                    continue
            request = CreateUserRequest(
                name=body.name,
                age=body.age,
                short_bio=body.short_bio,
                favorite_categories=categories,
            )
            return self.presenter.present(
                await self.action_runner.run(self.create_user_uc.execute, call=request),
            )

        @self.fast_api.get(
            "/users/{user_id}",
            tags=["users"],
            summary="Получить профиль пользователя",
        )
        async def get_user(user_id: int):
            return self.presenter.present(
                await self.action_runner.run(self.get_user_uc.execute, call=user_id),
            )

        @self.fast_api.put(
            "/users/{user_id}/bio",
            tags=["users"],
            summary="Обновить развёрнутое bio (онбординг, шаг 2)",
        )
        async def update_bio(user_id: int, body: UpdateBioBody):
            request = UpdateBioRequest(user_id=user_id, long_bio=body.long_bio)
            return self.presenter.present(
                await self.action_runner.run(self.update_bio_uc.execute, call=request),
            )

        @self.fast_api.post(
            "/users/{user_id}/onboarding/complete",
            tags=["users"],
            summary="Завершить онбординг (шаг 3)",
        )
        async def complete_onboarding(user_id: int):
            request = CompleteOnboardingRequest(user_id=user_id)
            return self.presenter.present(
                await self.action_runner.run(self.complete_onboarding_uc.execute, call=request),
            )

        @self.fast_api.post(
            "/users/{user_id}/avatar",
            tags=["users"],
            summary="Загрузить аватарку в S3 и привязать к профилю",
        )
        async def upload_avatar(
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
                data = await file.read()
                content_type = file.content_type or "image/jpeg"
                ext = (file.filename or "avatar.jpg").rsplit(".", 1)[-1]
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
