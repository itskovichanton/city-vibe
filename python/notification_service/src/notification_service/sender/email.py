"""Email-отправитель через aiosmtplib + Jinja2 шаблоны."""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Protocol

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.mybootstrap_ioc_itskovichanton.ioc import bean

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


class EmailSender(Protocol):
    async def send_otp(self, to: str, code: str, purpose: str) -> None: ...

    async def send_welcome(self, to: str, name: str) -> None: ...


@bean(
    host=("smtp.host", str, "localhost"),
    port=("smtp.port", int, 1025),
    user=("smtp.user", str, ""),
    password=("smtp.password", str, ""),
    from_address=("smtp.from", str, "noreply@cityvibe.local"),
    use_tls=("smtp.use_tls", bool, False),
)
class EmailSenderImpl(EmailSender):
    host: str = "localhost"
    port: int = 1025
    user: str = ""
    password: str = ""
    from_address: str = "noreply@cityvibe.local"
    use_tls: bool = False

    def init(self, **kwargs):
        self.host = kwargs.get("host", getattr(self, "host", "localhost"))
        self.port = int(kwargs.get("port", getattr(self, "port", 1025)))
        self.user = kwargs.get("user", getattr(self, "user", "")) or ""
        self.password = kwargs.get("password", getattr(self, "password", "")) or ""
        self.from_address = kwargs.get(
            "from_address",
            getattr(self, "from_address", "noreply@cityvibe.local"),
        )
        self.use_tls = bool(kwargs.get("use_tls", getattr(self, "use_tls", False)))
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def _send(self, to: str, subject: str, html: str, text: str = "") -> None:
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_address
        msg["To"] = to
        msg["Subject"] = subject
        if text:
            msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user or None,
                password=self.password or None,
                start_tls=self.use_tls,
            )
            logger.info("Email отправлен → %s | %s", to, subject)
        except Exception:
            logger.exception("Ошибка отправки email → %s", to)
            raise

    async def send_otp(self, to: str, code: str, purpose: str) -> None:
        titles = {"login": "Вход", "register": "Регистрация", "reset": "Сброс пароля"}
        title = titles.get(purpose, "Подтверждение")
        html = self._env.get_template("otp_email.html").render(code=code, purpose=title)
        text = f"CityVibe: ваш код {code}"
        await self._send(to, f"CityVibe — код {title}", html, text)

    async def send_welcome(self, to: str, name: str) -> None:
        html = self._env.get_template("welcome_email.html").render(name=name)
        await self._send(to, "Добро пожаловать в CityVibe!", html, f"Привет, {name}!")
