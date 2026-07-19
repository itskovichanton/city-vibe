from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

# Импорты нужны, чтобы @bean-классы зарегистрировались в IoC до inject()
from python.libs.clients.db import Database  # noqa: F401
from python.libs.clients.infra.events import RabbitMQEventBus  # noqa: F401
from python.libs.clients.infra.s3 import S3FileStorage  # noqa: F401
from python.libs.infra.outbox import OutboxImpl  # noqa: F401
from python.libs.infra.redis_client import RedisClientImpl  # noqa: F401
from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401
from python.user_service.src.user_service.presenter.server import Server
from python.user_service.src.user_service.repo.user import UserRepoImpl  # noqa: F401
from python.user_service.src.user_service.usecase.complete_onboarding import (  # noqa: F401
    CompleteOnboardingUseCaseImpl,
)
from python.user_service.src.user_service.usecase.create_user import CreateUserUseCaseImpl  # noqa: F401
from python.user_service.src.user_service.usecase.get_user import GetUserUseCaseImpl  # noqa: F401
from python.user_service.src.user_service.usecase.update_bio import UpdateBioUseCaseImpl  # noqa: F401


@bean
class UserServiceApp(Application):
    """Точка входа приложения user-service."""

    server: Server

    def run(self):
        self.server.start()
