"""Тесты OTP и паролей."""

import re

import pytest

from python.auth_service.src.auth_service.infra.otp_common import generate_otp_code
from python.auth_service.src.auth_service.infra.password import PasswordServiceImpl


def test_otp_format():
    code = generate_otp_code()
    assert re.fullmatch(r"\d{6}", code)


def test_password_hash_and_verify():
    svc = object.__new__(PasswordServiceImpl)
    hashed = svc.hash("MySecretPass123!")
    assert svc.verify("MySecretPass123!", hashed)
    assert not svc.verify("wrong", hashed)
