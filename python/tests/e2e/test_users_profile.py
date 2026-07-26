"""E2E users: bio, onboarding, avatar, soft-delete."""

from __future__ import annotations

import io

import httpx
import pytest

from python.tests.e2e.helpers import (
    MIN_PNG_BYTES,
    assert_http_error,
    delete_json,
    get_json,
    post_json,
    put_json,
    register_and_verify,
    unwrap,
)

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_user_onboarding_bio_avatar_delete(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]

    with httpx.Client(base_url=gateway, timeout=45.0) as client:
        user = register_and_verify(client, mailhog=mailhog, gender="female")
        user_id = user["user_id"]

        profile = get_json(client, f"/users/{user_id}")
        assert isinstance(profile, dict)
        assert profile.get("onboarding_completed") is False

        updated = put_json(
            client,
            f"/users/{user_id}/bio",
            {"long_bio": "Люблю вечерние прогулки и живую музыку."},
        )
        assert updated.get("long_bio", "").startswith("Люблю")

        completed = post_json(client, f"/users/{user_id}/onboarding/complete", {})
        assert completed.get("onboarding_completed") is True

        files = {"file": ("avatar.png", io.BytesIO(MIN_PNG_BYTES), "image/png")}
        r = client.post(f"/users/{user_id}/avatar", files=files)
        try:
            data = r.json()
        except Exception:
            pytest.fail(f"avatar: HTTP {r.status_code}, non-JSON: {r.text[:300]}")
        if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
            pytest.fail(f"avatar upload failed: {data}")
        avatar_out = unwrap(data)
        assert isinstance(avatar_out, dict)
        refreshed = get_json(client, f"/users/{user_id}")
        assert isinstance(refreshed, dict)
        assert refreshed.get("avatar_url") or avatar_out.get("avatar_url")

        deleted = delete_json(client, f"/users/{user_id}")
        assert deleted.get("ok") is True
        assert int(deleted.get("user_id", user_id)) == user_id

        # Soft-deleted пользователь больше не отдаётся get_by_id
        assert_http_error(client, "get", f"/users/{user_id}")


@pytest.mark.e2e
def test_user_not_found(live_backend):
    gateway = live_backend["gateway"]
    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        assert_http_error(client, "get", "/users/999999999")
