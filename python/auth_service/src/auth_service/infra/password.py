"""Хеширование паролей (argon2 через pwdlib)."""

from typing import Protocol

from pwdlib import PasswordHash
from src.mybootstrap_ioc_itskovichanton.ioc import bean

_hasher = PasswordHash.recommended()


class PasswordService(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


@bean
class PasswordServiceImpl(PasswordService):
    def hash(self, password: str) -> str:
        return _hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return _hasher.verify(password, password_hash)
