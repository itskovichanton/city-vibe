"""События auth / notification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthOtpRequestedEvent:
    """Нужно отправить OTP (SMS или email)."""

    challenge_id: str
    purpose: str  # login | register | reset
    channel: str  # sms | email
    destination: str  # E.164 или email
    code: str  # для MVP; mock/SMTP
    locale: str = "ru"


@dataclass
class AuthUserRegisteredEvent:
    """Регистрация завершена (профиль уже создан синхронно)."""

    user_id: int
    account_id: int
    email: Optional[str] = None
    phone: Optional[str] = None
    name: str = ""


TOPIC_AUTH_OTP_REQUESTED = "auth.otp.requested"
TOPIC_AUTH_USER_REGISTERED = "auth.user.registered"
