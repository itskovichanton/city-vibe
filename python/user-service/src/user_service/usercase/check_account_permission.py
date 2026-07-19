from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException, ERR_REASON_ACCESS_DENIED
from src.mybootstrap_pyauth_itskovichanton.entities import Session, User

from src.paas.backend.repo.user_permission import UserPermissionRepo


class CheckAccountPermissionUseCase(Protocol):

    def check_permission(self, account: int | Session | User, action, *arg):
        ...


@bean
class CheckAccountPermissionUseCaseImpl(CheckAccountPermissionUseCase):
    user_permission_repo: UserPermissionRepo

    def _fail(self, action):
        raise CoreException(message=f"У пользователя нет прав на выполнение действия {action}",
                            reason=ERR_REASON_ACCESS_DENIED)

    def check_permission(self, auth_arg: int | Session | User, action, *arg):
        if not self.user_permission_repo.has_permission(self.get_account_id(auth_arg, action), *arg):
            self._fail(action)

    def get_account_id(self, auth_arg, action):
        if not auth_arg:
            self._fail(action)
        if isinstance(auth_arg, Session):
            auth_arg = auth_arg.account
        if not auth_arg:
            self._fail(action)
        if isinstance(auth_arg, (User,)):
            auth_arg = auth_arg.id
        if not isinstance(auth_arg, int):
            self._fail(action)
        return auth_arg
