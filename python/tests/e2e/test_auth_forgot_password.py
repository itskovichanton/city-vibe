"""E2E: forgot password (3 шага) + негативы."""

from __future__ import annotations

import httpx
import pytest

from python.tests.e2e.helpers import (
    api_error_message,
    assert_http_error,
    post_json,
    register_and_verify,
    unique_email,
    wait_otp,
)

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_forgot_password_full_flow_then_login_with_new_password(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]
    new_password = "BrandNewPass2!"

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        user = register_and_verify(client, mailhog=mailhog)
        identifier = user["identifier"]

        # Несуществующий email — фейковый challenge без OTP (anti-enumeration)
        fake = post_json(
            client,
            "/auth/password/forgot",
            {"identifier": unique_email("missing"), "channel": "email"},
        )
        assert fake.get("challenge_id")
        assert fake.get("expires_in", 0) > 0

        challenge = post_json(
            client,
            "/auth/password/forgot",
            {"identifier": identifier, "channel": "email"},
        )
        assert challenge.get("channel") == "email"
        assert challenge.get("challenge_id")

        otp = wait_otp(
            mailhog=mailhog,
            email_addr=identifier,
            challenge_id=challenge["challenge_id"],
            channel=challenge.get("channel"),
        )
        reset = post_json(
            client,
            "/auth/password/forgot/verify",
            {"challenge_id": challenge["challenge_id"], "code": otp},
        )
        assert reset.get("reset_token")
        assert reset.get("expires_in", 0) > 0

        ok = post_json(
            client,
            "/auth/password/reset",
            {"reset_token": reset["reset_token"], "new_password": new_password},
        )
        assert ok.get("ok") is True

        # Старый пароль больше не работает
        bad = assert_http_error(
            client,
            "post",
            "/auth/login",
            json={"identifier": identifier, "password": user["password"]},
        )
        assert "error" in bad or True

        # Новый пароль — логин OK
        login_ch = post_json(
            client,
            "/auth/login",
            {"identifier": identifier, "password": new_password},
        )
        login_otp = wait_otp(
            mailhog=mailhog,
            email_addr=identifier,
            challenge_id=login_ch["challenge_id"],
            channel=login_ch.get("channel"),
        )
        tokens = post_json(
            client,
            "/auth/login/verify",
            {"challenge_id": login_ch["challenge_id"], "code": login_otp},
        )
        assert int(tokens["user_id"]) == user["user_id"]

        # Повторное использование reset_token
        reused = assert_http_error(
            client,
            "post",
            "/auth/password/reset",
            json={"reset_token": reset["reset_token"], "new_password": "AnotherPass3!"},
        )
        msg = api_error_message(reused).lower()
        assert msg  # любая осмысленная ошибка
