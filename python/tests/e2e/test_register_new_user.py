"""
E2E: регистрация нового пользователя через api-gateway.

Реальный стек: docker infra + user/auth/place/notification/... + gateway.
Флоу: POST /auth/register → OTP из MailHog → POST /auth/register/verify → GET /users/{id}
+ проверка строк в Postgres (users + accounts/identities).
"""

from __future__ import annotations

import re
import uuid

import httpx
import pytest

from python.tests.e2e.helpers import (
    api_error_message,
    get_json,
    post_json,
    psql,
    wait_otp_from_mailhog,
)

pytestmark = pytest.mark.e2e


@pytest.mark.e2e
def test_register_new_user_otp_creates_filled_profile(live_backend):
    gateway = live_backend["gateway"]
    mailhog = live_backend["mailhog"]
    compose = live_backend["compose_file"]

    unique = uuid.uuid4().hex[:12]
    email_addr = f"e2e.register.{unique}@example.com"
    name = f"E2E User {unique}"
    password = "SecurePass1!"
    birthdate = "1995-04-12"
    gender = "female"

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        cities = get_json(client, "/cities")
        assert isinstance(cities, list) and cities, "GET /cities должен вернуть города"
        city_id = int(cities[0]["id"])
        assert city_id > 0

        existing = psql(
            compose,
            "cityvibe_auth",
            f"SELECT count(*) FROM identities WHERE type='email' AND value='{email_addr}';",
        )
        assert existing == "0", f"email уже есть в auth DB: {email_addr}"

        challenge = post_json(
            client,
            "/auth/register",
            {
                "name": name,
                "identifier": email_addr,
                "password": password,
                "city_id": city_id,
                "accept_terms": True,
                "birthdate": birthdate,
                "gender": gender,
            },
        )
        assert challenge.get("channel") == "email"
        assert challenge.get("challenge_id")
        assert challenge.get("expires_in", 0) > 0

        pending = psql(
            compose,
            "cityvibe_auth",
            "SELECT a.id, a.status, a.name, a.city_id, a.birthdate, a.accept_terms, a.gender "
            "FROM accounts a "
            f"JOIN identities i ON i.account_id = a.id "
            f"WHERE i.type='email' AND i.value='{email_addr}';",
        )
        assert pending, "pending account не создан"
        parts = pending.split("|")
        account_id = int(parts[0])
        assert parts[1] == "pending"
        assert parts[2] == name
        assert int(parts[3]) == city_id
        assert parts[4] == birthdate
        assert parts[5] in {"t", "true", "1"}
        assert parts[6] == gender

        otp = wait_otp_from_mailhog(mailhog, email_addr)
        assert re.fullmatch(r"\d{6}", otp), "OTP должен быть 6 цифр"

        tokens = post_json(
            client,
            "/auth/register/verify",
            {"challenge_id": challenge["challenge_id"], "code": otp},
        )
        assert tokens.get("access_token")
        assert tokens.get("refresh_token")
        assert tokens.get("token_type") == "Bearer"
        user_id = int(tokens["user_id"])
        token_account_id = int(tokens["account_id"])
        assert user_id > 0
        assert token_account_id == account_id

        active = psql(
            compose,
            "cityvibe_auth",
            f"SELECT status, user_id FROM accounts WHERE id={account_id};",
        )
        status, linked_user = active.split("|")
        assert status == "active"
        assert int(linked_user) == user_id

        verified = psql(
            compose,
            "cityvibe_auth",
            f"SELECT verified FROM identities WHERE account_id={account_id} AND type='email';",
        )
        assert verified in {"t", "true", "1"}

        user = get_json(client, f"/users/{user_id}")
        assert isinstance(user, dict)
        assert int(user["id"]) == user_id
        assert user["name"] == name
        assert user.get("deleted") is False
        assert user.get("onboarding_completed") is False
        assert int(user["city_id"]) == city_id
        assert str(user["birthdate"])[:10] == birthdate
        assert user.get("gender") == gender
        assert int(user["auth_account_id"]) == account_id

        db_user = psql(
            compose,
            "cityvibe_users",
            "SELECT name, city_id, birthdate, auth_account_id, deleted, onboarding_completed, gender "
            f"FROM users WHERE id={user_id};",
        )
        assert db_user, f"user id={user_id} не найден в cityvibe_users"
        uname, ucity, ubirth, uauth, udeleted, uonb, ugender = db_user.split("|")
        assert uname == name
        assert int(ucity) == city_id
        assert ubirth == birthdate
        assert int(uauth) == account_id
        assert udeleted in {"f", "false", "0"}
        assert uonb in {"f", "false", "0"}
        assert ugender == gender

        r = client.post(
            "/auth/register",
            json={
                "name": "Dup",
                "identifier": email_addr,
                "password": password,
                "city_id": city_id,
                "accept_terms": True,
                "gender": gender,
            },
        )
        dup = r.json()
        assert r.status_code >= 400 or "error" in dup
        msg = api_error_message(dup).lower()
        assert "существует" in msg or "already" in msg
