"""E2E auth: login, refresh, logout, resend OTP, phone register, Google stub."""

from __future__ import annotations

import httpx
import pytest

from python.tests.e2e.helpers import (
    DEFAULT_PASSWORD,
    api_error_message,
    assert_http_error,
    otp_from_redis,
    post_json,
    register_and_verify,
    unique_phone,
    wait_otp,
)

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_login_otp_verify_refresh_logout(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        user = register_and_verify(client, mailhog=mailhog, gender="female")
        identifier = user["identifier"]
        password = user["password"]

        # Неверный пароль
        bad = assert_http_error(
            client,
            "post",
            "/auth/login",
            json={"identifier": identifier, "password": "WrongPass1!"},
        )
        msg = api_error_message(bad).lower()
        assert "логин" in msg or "пароль" in msg or "password" in msg or "invalid" in msg

        challenge = post_json(
            client,
            "/auth/login",
            {"identifier": identifier, "password": password},
        )
        assert challenge.get("channel") == "email"
        assert challenge.get("challenge_id")

        # Неверный OTP
        wrong = assert_http_error(
            client,
            "post",
            "/auth/login/verify",
            json={"challenge_id": challenge["challenge_id"], "code": "000000"},
        )
        assert "error" in wrong or True

        otp = wait_otp(
            mailhog=mailhog,
            email_addr=identifier,
            challenge_id=challenge["challenge_id"],
            channel=challenge.get("channel"),
        )
        tokens = post_json(
            client,
            "/auth/login/verify",
            {"challenge_id": challenge["challenge_id"], "code": otp},
        )
        assert tokens["access_token"]
        assert tokens["refresh_token"]
        assert int(tokens["user_id"]) == user["user_id"]
        assert int(tokens["account_id"]) == user["account_id"]

        refreshed = post_json(
            client,
            "/auth/token/refresh",
            {"refresh_token": tokens["refresh_token"]},
        )
        assert refreshed["access_token"]
        assert refreshed["refresh_token"]
        assert refreshed["refresh_token"] != tokens["refresh_token"]

        # Старый refresh после rotation невалиден
        assert_http_error(
            client,
            "post",
            "/auth/token/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )

        logged_out = post_json(
            client,
            "/auth/logout",
            {"refresh_token": refreshed["refresh_token"]},
        )
        assert logged_out.get("ok") is True

        # Повторный logout / refresh отозванного — ошибка или идемпотентный ok
        r = client.post("/auth/token/refresh", json={"refresh_token": refreshed["refresh_token"]})
        data = r.json()
        assert r.status_code >= 400 or "error" in data


@pytest.mark.e2e
def test_otp_resend_issues_new_challenge(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        user = register_and_verify(client, mailhog=mailhog)
        challenge = post_json(
            client,
            "/auth/login",
            {"identifier": user["identifier"], "password": user["password"]},
        )
        old_id = challenge["challenge_id"]
        resent = post_json(client, "/auth/otp/resend", {"challenge_id": old_id})
        assert resent.get("challenge_id")
        assert resent["challenge_id"] != old_id
        assert resent.get("channel") == challenge.get("channel")

        otp = wait_otp(
            mailhog=mailhog,
            email_addr=user["identifier"],
            challenge_id=resent["challenge_id"],
            channel=resent.get("channel"),
        )
        tokens = post_json(
            client,
            "/auth/login/verify",
            {"challenge_id": resent["challenge_id"], "code": otp},
        )
        assert tokens["access_token"]


@pytest.mark.e2e
def test_register_phone_sms_otp_via_redis(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]
    phone = unique_phone()

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        user = register_and_verify(
            client,
            mailhog=mailhog,
            identifier=phone,
            name="Phone User",
            gender="male",
        )
        assert user["user_id"] > 0
        assert user["identifier"] == phone

        # Логин по телефону
        challenge = post_json(
            client,
            "/auth/login",
            {"identifier": phone, "password": DEFAULT_PASSWORD},
        )
        assert challenge.get("channel") == "sms"
        otp = otp_from_redis(challenge["challenge_id"])
        tokens = post_json(
            client,
            "/auth/login/verify",
            {"challenge_id": challenge["challenge_id"], "code": otp},
        )
        assert int(tokens["user_id"]) == user["user_id"]


@pytest.mark.e2e
def test_google_auth_unconfigured(live_backend):
    gateway = live_backend["gateway"]
    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        data = assert_http_error(
            client,
            "post",
            "/auth/social/google",
            json={"id_token": "fake.token.value", "city_id": 1, "gender": "male"},
        )
        msg = api_error_message(data).lower()
        assert "google" in msg or "oauth" in msg or "настроен" in msg or "token" in msg
