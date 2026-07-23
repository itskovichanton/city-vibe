"""HTTP-клиент design-service."""

from __future__ import annotations

from typing import Any, Protocol

from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_fastapi_itskovichanton.client.http import on_mbclient_api

api_call = on_mbclient_api(_name="clients.design_service")


class DesignServiceClient(Protocol):
    def health(self) -> Any: ...

    def list_pin_styles(self) -> Any: ...

    def get_default_pin_style(self) -> Any: ...

    def get_pin_style(self, style_id: int) -> Any: ...

    def list_chat_themes(self) -> Any: ...

    def get_default_chat_theme(self) -> Any: ...

    def get_chat_theme(self, theme_id: int) -> Any: ...


@bean
class DesignServiceClientImpl(DesignServiceClient):
    @api_call
    def health(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/health", timeout=30, headers=headers)

    @api_call
    def list_pin_styles(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/pin-styles", timeout=30, headers=headers)

    @api_call
    def get_default_pin_style(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/pin-styles/default", timeout=30, headers=headers)

    @api_call
    def get_pin_style(self, style_id: int, session=None, url=None, headers=None):
        return session.get(url=f"{url}/pin-styles/{style_id}", timeout=30, headers=headers)

    @api_call
    def list_chat_themes(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/chat-themes", timeout=30, headers=headers)

    @api_call
    def get_default_chat_theme(self, session=None, url=None, headers=None):
        return session.get(url=f"{url}/chat-themes/default", timeout=30, headers=headers)

    @api_call
    def get_chat_theme(self, theme_id: int, session=None, url=None, headers=None):
        return session.get(url=f"{url}/chat-themes/{theme_id}", timeout=30, headers=headers)
