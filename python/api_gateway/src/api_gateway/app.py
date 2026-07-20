from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401
from python.api_gateway.src.api_gateway.presenter.server import Server


@bean
class ApiGatewayApp(Application):
    server: Server

    def run(self):
        self.server.start()
