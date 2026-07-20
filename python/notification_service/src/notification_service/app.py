from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database  # noqa: F401
from python.libs.clients.infra.events import RabbitMQEventBus  # noqa: F401
from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401
from python.notification_service.src.notification_service.presenter.server import Server
from python.notification_service.src.notification_service.sender.email import EmailSenderImpl  # noqa: F401
from python.libs.clients.domain.mock_notify.client import MockNotifyClient  # noqa: F401
from python.libs.clients.domain.mock_notify.client import MockNotifyClientImpl  # noqa: F401
from python.notification_service.src.notification_service.sender.sms import SmsSenderImpl  # noqa: F401
from python.notification_service.src.notification_service.worker.notification_worker import (  # noqa: F401
    NotificationWorker,
)


@bean
class NotificationServiceApp(Application):
    server: Server

    def run(self):
        self.server.start()
