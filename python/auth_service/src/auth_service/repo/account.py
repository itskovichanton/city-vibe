"""Репозиторий аккаунтов auth-service."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional, Protocol

from sqlalchemy import select
from src.mybootstrap_ioc_itskovichanton.ioc import bean

from python.libs.clients.db import Database
from python.auth_service.src.auth_service.infra.orm.models import (
    AccountModel,
    IdentityModel,
    OAuthAccountModel,
    RefreshTokenModel,
)


class AccountRepo(Protocol):
    async def create_pending(
        self,
        *,
        name: str,
        password_hash: str,
        identity_type: str,
        identity_value: str,
        birthdate: Optional[date],
        city_id: Optional[int],
        accept_terms: bool,
    ) -> AccountModel: ...

    async def get_by_id(self, account_id: int) -> Optional[AccountModel]: ...

    async def find_by_identity(self, identity_type: str, value: str) -> Optional[AccountModel]: ...

    async def activate(self, account_id: int, user_id: int) -> AccountModel: ...

    async def save_refresh_token(self, account_id: int, token_hash: str, expires_at: datetime) -> None: ...

    async def find_refresh_token(self, token_hash: str) -> Optional[RefreshTokenModel]: ...

    async def revoke_refresh_token(self, token_hash: str) -> None: ...

    async def find_oauth(self, provider: str, provider_user_id: str) -> Optional[AccountModel]: ...

    async def link_oauth(
        self, account_id: int, provider: str, provider_user_id: str, email: Optional[str]
    ) -> None: ...

    async def update_password(self, account_id: int, password_hash: str) -> None: ...


@bean
class AccountRepoImpl(AccountRepo):
    db: Database

    async def create_pending(
        self,
        *,
        name: str,
        password_hash: str,
        identity_type: str,
        identity_value: str,
        birthdate: Optional[date],
        city_id: Optional[int],
        accept_terms: bool,
    ) -> AccountModel:
        async with self.db.session() as session:
            account = AccountModel(
                name=name,
                password_hash=password_hash,
                status="pending",
                birthdate=birthdate,
                city_id=city_id,
                accept_terms=accept_terms,
            )
            session.add(account)
            await session.flush()
            identity = IdentityModel(
                account_id=account.id,
                type=identity_type,
                value=identity_value,
                verified=False,
                is_primary=True,
            )
            session.add(identity)
            await session.flush()
            await session.refresh(account)
            return account

    async def get_by_id(self, account_id: int) -> Optional[AccountModel]:
        async with self.db.session() as session:
            model = await session.get(AccountModel, account_id)
            if model is None or model.deleted:
                return None
            return model

    async def find_by_identity(self, identity_type: str, value: str) -> Optional[AccountModel]:
        async with self.db.session() as session:
            stmt = (
                select(AccountModel)
                .join(IdentityModel, IdentityModel.account_id == AccountModel.id)
                .where(
                    IdentityModel.type == identity_type,
                    IdentityModel.value == value,
                    AccountModel.deleted.is_(False),
                )
            )
            return (await session.execute(stmt)).scalar_one_or_none()

    async def activate(self, account_id: int, user_id: int) -> AccountModel:
        async with self.db.session() as session:
            account = await session.get(AccountModel, account_id)
            if account is None:
                raise ValueError("account not found")
            account.user_id = user_id
            account.status = "active"
            for ident in account.identities:
                ident.verified = True
            await session.flush()
            await session.refresh(account)
            return account

    async def save_refresh_token(self, account_id: int, token_hash: str, expires_at: datetime) -> None:
        async with self.db.session() as session:
            session.add(
                RefreshTokenModel(account_id=account_id, token_hash=token_hash, expires_at=expires_at)
            )

    async def find_refresh_token(self, token_hash: str) -> Optional[RefreshTokenModel]:
        async with self.db.session() as session:
            stmt = select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
            )
            return (await session.execute(stmt)).scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        async with self.db.session() as session:
            stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row:
                row.revoked_at = datetime.now(timezone.utc)

    async def find_oauth(self, provider: str, provider_user_id: str) -> Optional[AccountModel]:
        async with self.db.session() as session:
            stmt = (
                select(AccountModel)
                .join(OAuthAccountModel, OAuthAccountModel.account_id == AccountModel.id)
                .where(
                    OAuthAccountModel.provider == provider,
                    OAuthAccountModel.provider_user_id == provider_user_id,
                    AccountModel.deleted.is_(False),
                )
            )
            return (await session.execute(stmt)).scalar_one_or_none()

    async def link_oauth(
        self, account_id: int, provider: str, provider_user_id: str, email: Optional[str]
    ) -> None:
        async with self.db.session() as session:
            session.add(
                OAuthAccountModel(
                    account_id=account_id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    email=email,
                )
            )

    async def update_password(self, account_id: int, password_hash: str) -> None:
        async with self.db.session() as session:
            account = await session.get(AccountModel, account_id)
            if account is None:
                raise ValueError("account not found")
            account.password_hash = password_hash
