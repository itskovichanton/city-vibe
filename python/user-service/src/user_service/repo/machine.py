from typing import Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean

from src.paas.backend.repo.db import DB


class MachineRepo(Protocol):

    def get_team(self, ip: str):
        ...


@bean
class MachineRepoImpl(MachineRepo):
    db: DB

    def get_team(self, ip: str):
        q = """select u.id, u.username, u.email, u.name, u.telegram_username, usr.user_role from public.user u
        inner join public.user_machine_roles usr on usr.user_id=u.id
        where usr.ip = %s"""

        return self.db.exec_sql(query=q, params=[ip])
