"""Юнит-тесты S3FileStorage.normalize_key."""

from python.libs.clients.infra.s3.storage import S3FileStorage


def test_normalize_key_from_legacy_url():
    key = S3FileStorage.normalize_key(
        "http://localhost:9000/city-vibe/avatars/45/abc.jpg",
        bucket="city-vibe",
    )
    assert key == "avatars/45/abc.jpg"


def test_normalize_key_from_storage_key():
    assert S3FileStorage.normalize_key("avatars/45/abc.jpg", bucket="city-vibe") == "avatars/45/abc.jpg"
