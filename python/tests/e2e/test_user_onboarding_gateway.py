"""E2E: онбординг (PATCH profile, bio, complete) и аккаунт Миланы."""

from __future__ import annotations

import httpx
import pytest

from python.tests.e2e.helpers import (
    get_json,
    patch_json,
    post_json,
    put_json,
    register_and_verify,
)

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_patch_user_profile(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]

    with httpx.Client(base_url=gateway, timeout=45.0) as client:
        user = register_and_verify(client, mailhog=mailhog)
        user_id = user["user_id"]

        updated = patch_json(
            client,
            f"/users/{user_id}",
            {
                "name": "Мария",
                "favorite_categories": ["cafes", "parks", "invalid_code"],
            },
        )
        assert updated.get("name") == "Мария"
        assert "cafes" in (updated.get("favorite_categories") or [])
        assert "parks" in (updated.get("favorite_categories") or [])
        assert "invalid_code" not in (updated.get("favorite_categories") or [])


@pytest.mark.e2e
def test_get_milana_account(live_backend):
    gateway = live_backend["gateway"]

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        milana = get_json(client, "/milana/account")
        assert isinstance(milana, dict)
        assert milana.get("name") == "Милана"
        assert str(milana.get("role", "")).upper() == "MILANA"
        assert milana.get("onboarding_completed") is True


@pytest.mark.e2e
def test_onboarding_flow_patch_bio_complete(live_backend):
    """Порядок как в мобилке: PATCH profile → PUT bio → POST complete."""
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]

    with httpx.Client(base_url=gateway, timeout=45.0) as client:
        user = register_and_verify(client, mailhog=mailhog, gender="female")
        user_id = user["user_id"]

        profile = get_json(client, f"/users/{user_id}")
        assert profile.get("onboarding_completed") is False

        step1 = patch_json(
            client,
            f"/users/{user_id}",
            {
                "name": "Ольга",
                "favorite_categories": ["bars", "theaters"],
            },
        )
        assert step1.get("name") == "Ольга"
        assert step1.get("onboarding_completed") is False

        step2 = put_json(
            client,
            f"/users/{user_id}/bio",
            {"long_bio": "Люблю театры и вечерние бары."},
        )
        assert "театры" in step2.get("long_bio", "")

        done = post_json(client, f"/users/{user_id}/onboarding/complete", {})
        assert done.get("onboarding_completed") is True
        assert "bars" in (done.get("favorite_categories") or [])
        assert "theaters" in (done.get("favorite_categories") or [])

        milana = get_json(client, "/milana/account")
        assert milana.get("name") == "Милана"
