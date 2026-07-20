from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database  # noqa: F401
from python.libs.clients.infra.events import RabbitMQEventBus  # noqa: F401
from python.libs.infra.outbox import OutboxImpl  # noqa: F401
from python.libs.infra.redis_client import RedisClientImpl  # noqa: F401
from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401
from python.auth_service.src.auth_service.infra.jwt_service import JwtServiceImpl  # noqa: F401
from python.auth_service.src.auth_service.infra.otp_store import RedisAuthOtpStore  # noqa: F401
from python.auth_service.src.auth_service.infra.password import PasswordServiceImpl  # noqa: F401
from python.libs.clients.domain.user_service.client import UserServiceClientImpl  # noqa: F401
from python.auth_service.src.auth_service.presenter.server import Server
from python.auth_service.src.auth_service.repo.account import AccountRepoImpl  # noqa: F401
from python.auth_service.src.auth_service.usecase.auth_flow import AuthUseCaseImpl  # noqa: F401


@bean
class AuthServiceApp(Application):
    """Точка входа auth-service."""

    server: Server

    def run(self):
        self.server.start()
