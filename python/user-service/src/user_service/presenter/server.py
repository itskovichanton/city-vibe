import uvicorn
from fastapi import FastAPI
from src.mbulak_tools.infra_middleware import InfraFastAPISupport
from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.config import ConfigService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_ioc_itskovichanton.utils import default_dataclass_field
from src.mybootstrap_mvc_fastapi_itskovichanton.error_handler import ErrorHandlerFastAPISupport
from src.mybootstrap_mvc_fastapi_itskovichanton.presenters import JSONResultPresenterImpl
from src.mybootstrap_mvc_itskovichanton.result_presenter import ResultPresenter
from src.mybootstrap_pyauth_itskovichanton.frontend.support import AuthFastAPISupport
from src.mybootstrap_pyauth_itskovichanton.frontend.utils import get_caller_from_request
from starlette.requests import Request
from starlette.staticfiles import StaticFiles


@bean(port=("server.port", int, 8082), host=("server.host", str, "0.0.0.0"))
class Server:
    config_service: ConfigService
    error_handler_fast_api_support: ErrorHandlerFastAPISupport
    auth_support: AuthFastAPISupport
    presenter: ResultPresenter = default_dataclass_field(JSONResultPresenterImpl(exclude_unset=True))
    logger_service: LoggerService
    infra_support: InfraFastAPISupport

    def init(self, **kwargs):
        self.fast_api = self.init_fast_api()
        self.add_routes()

    def start(self):
        uvicorn.run(self.fast_api, port=self.port, host=self.host)

    def init_fast_api(self) -> FastAPI:
        r = FastAPI(title='paasadmin', debug=False)
        r.mount("/static", StaticFiles(directory=self.config_service.dir("static")), name="static")
        self.error_handler_fast_api_support.mount(r)
        self.auth_support.mount(r)
        self.infra_support.mount(r)
        return r

    def add_routes(self):
        @self.fast_api.get("/deploy/{action}")
        async def execute_action_on_deploy(request: Request, deploy_name: str, machine: str, action: str):
            return self.presenter.present(
                await self.controller.execute_action_on_deploy(
                    get_caller_from_request(request), deploy_name, action, machine,
                ),
            )

        @self.fast_api.get("/machine/team")
        async def get_machine_team(request: Request, ip):
            return self.presenter.present(
                await self.controller.get_machine_team(caller=get_caller_from_request(request), ip=ip),
            )
