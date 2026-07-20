"""Тесты parse_identifier / mask_identifier."""

import pytest

from python.libs.infra.identifier import IdentifierType, mask_identifier, parse_identifier


def test_parse_email():
    p = parse_identifier("User@Example.COM")
    assert p.type == IdentifierType.EMAIL
    assert p.value == "user@example.com"


def test_parse_phone_ru():
    p = parse_identifier("+7 999 123-45-67")
    assert p.type == IdentifierType.PHONE
    assert p.value.startswith("+7")


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        parse_identifier("not-an-identifier")


def test_mask_email():
    p = parse_identifier("alex@test.ru")
    masked = mask_identifier(p)
    assert "@test.ru" in masked
    assert "alex" not in masked


def test_mask_phone():
    p = parse_identifier("+79991234567")
    masked = mask_identifier(p)
    assert "***" in masked
