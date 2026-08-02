from src.mybootstrap_core_itskovichanton.app import Application
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.design_service.src.design_service.presenter.server import Server
from python.design_service.src.design_service.repo.chat_theme import ChatThemeRepoImpl  # noqa: F401
from python.design_service.src.design_service.repo.pin_style import PinStyleRepoImpl  # noqa: F401
from python.design_service.src.design_service.usecase.chat_themes import (  # noqa: F401
    GetChatThemeUseCaseImpl,
    GetDefaultChatThemeUseCaseImpl,
    ListChatThemesUseCaseImpl,
)
from python.design_service.src.design_service.usecase.pin_styles import (  # noqa: F401
    GetDefaultPinStyleUseCaseImpl,
    GetPinStyleUseCaseImpl,
    ListPinStylesUseCaseImpl,
)
from python.libs.clients.db import Database  # noqa: F401
from python.libs.infra.support import CityVibeInfraSupport  # noqa: F401


@bean
class DesignServiceApp(Application):
    server: Server

    def run(self):
        self.server.start()
