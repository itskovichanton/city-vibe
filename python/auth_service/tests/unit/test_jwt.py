"""Тесты JWT auth-service."""

from datetime import datetime, timezone

import jwt
import pytest

from python.auth_service.src.auth_service.infra.jwt_service import JwtServiceImpl  # noqa: E402


class FakeConfig:
    def get(self, key, default=None):
        if key == "auth":
            return {"jwt_secret": "test-secret", "access_ttl_min": 15, "refresh_ttl_days": 30}
        return default


@pytest.fixture
def jwt_svc():
    svc = object.__new__(JwtServiceImpl)
    svc.init(jwt_secret="test-secret", access_ttl_min=15, refresh_ttl_days=30)
    return svc


def test_access_token_roundtrip(jwt_svc):
    token, expires = jwt_svc.create_access_token(123)
    assert expires == 15 * 60
    payload = jwt_svc.decode_access_token(token)
    assert payload["sub"] == "123"
    assert payload["type"] == "access"


def test_refresh_token_hash(jwt_svc):
    raw, hashed, expires = jwt_svc.create_refresh_token()
    assert len(raw) > 20
    assert jwt_svc.hash_refresh_token(raw) == hashed
    assert expires > datetime.now(timezone.utc)
