from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database  # noqa: F401
from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401
from python.place_catalog.src.place_catalog.presenter.server import Server
from python.place_catalog.src.place_catalog.repo.city import CityRepoImpl  # noqa: F401


@bean
class PlaceCatalogApp(Application):
    """Точка входа place-catalog."""

    server: Server

    def run(self):
        self.server.start()
