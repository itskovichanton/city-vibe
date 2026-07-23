from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database  # noqa: F401
from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401
from python.place_service.src.place_service.presenter.server import Server
from python.place_service.src.place_service.repo.attr_schema import AttrSchemaRepoImpl  # noqa: F401
from python.place_service.src.place_service.repo.category import CategoryRepoImpl  # noqa: F401
from python.place_service.src.place_service.repo.city import CityRepoImpl  # noqa: F401
from python.place_service.src.place_service.repo.place import PlaceRepoImpl  # noqa: F401
from python.place_service.src.place_service.repo.place_search import PlaceSearchRepoImpl  # noqa: F401


@bean
class PlaceServiceApp(Application):
    """Точка входа place-service."""

    server: Server

    def run(self):
        self.server.start()
