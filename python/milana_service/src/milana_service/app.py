from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.milana_service.src.milana_service.agent.places_nl_search import PlacesNlSearchAgent  # noqa: F401
from python.milana_service.src.milana_service.infra.deepseek import DeepSeekClient  # noqa: F401
from python.milana_service.src.milana_service.infra.place_search_client import PlaceSearchHttpClient  # noqa: F401
from python.milana_service.src.milana_service.presenter.server import Server
from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401


@bean
class MilanaServiceApp(Application):
    server: Server

    def run(self):
        self.server.start()
