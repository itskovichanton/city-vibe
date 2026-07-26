"""
E2E: регистрация нового пользователя через api-gateway.

Реальный стек: docker infra + user/auth/place/notification/... + gateway.
Флоу: POST /auth/register → OTP из MailHog → POST /auth/register/verify → GET /users/{id}
+ проверка строк в Postgres (users + accounts/identities).
"""

from __future__ import annotations

import base64
import email
import re
import subprocess
import time
import uuid
from email import policy
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.e2e


def _unwrap(payload: dict | list) -> dict | list:
    if isinstance(payload, dict) and "result" in payload:
        return payload["result"]
    return payload


def _api_error_message(payload: dict) -> str:
    err = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(err, dict):
        return str(err.get("message") or err)
    return str(payload)


def _post_json(client: httpx.Client, path: str, body: dict) -> dict:
    r = client.post(path, json=body)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON body: {r.text[:300]}")
    if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
        pytest.fail(f"{path}: HTTP {r.status_code}: {_api_error_message(data)}")
    out = _unwrap(data)
    assert isinstance(out, dict), f"{path}: ожидался object, получили {type(out)}"
    return out


def _get_json(client: httpx.Client, path: str) -> dict | list:
    r = client.get(path)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON body: {r.text[:300]}")
    if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
        pytest.fail(f"{path}: HTTP {r.status_code}: {_api_error_message(data)}")
    return _unwrap(data)


def _extract_otp_from_mailhog_item(item: dict) -> str | None:
    """Достаёт 6-значный OTP из MIME/base64 тела MailHog."""
    content = item.get("Content") or {}
    candidates: list[str] = []

    body = content.get("Body") or ""
    if body:
        candidates.append(body)

    mime = content.get("MIME") or item.get("MIME") or {}
    for part in mime.get("Parts") or []:
        part_body = (part.get("Body") if isinstance(part, dict) else None) or ""
        if part_body:
            candidates.append(part_body)
        headers = (part.get("Headers") if isinstance(part, dict) else None) or {}
        cte = " ".join(headers.get("Content-Transfer-Encoding") or []).lower()
        if "base64" in cte and part_body:
            try:
                candidates.append(base64.b64decode(part_body).decode("utf-8", "replace"))
            except Exception:
                pass

    # Полный MIME-разбор multipart
    raw = item.get("Raw") or {}
    raw_data = raw.get("Data") if isinstance(raw, dict) else None
    if raw_data:
        try:
            msg = email.message_from_string(raw_data, policy=policy.default)
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                try:
                    candidates.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        candidates.append(payload.decode("utf-8", "replace"))
        except Exception:
            pass

    for text in candidates:
        if not isinstance(text, str):
            continue
        # «CityVibe: ваш код 123456» или HTML с крупными цифрами
        m = re.search(r"(?:код|code)\s*[:=]?\s*(\d{6})", text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"(?<!\d)(\d{6})(?!\d)", text)
        if m:
            return m.group(1)
    return None


def _wait_otp_from_mailhog(mailhog: str, email_addr: str, timeout_sec: float = 30.0) -> str:
    mailbox, _, domain = email_addr.partition("@")
    deadline = time.time() + timeout_sec
    last_total = -1
    while time.time() < deadline:
        r = httpx.get(f"{mailhog}/api/v2/messages", timeout=5.0)
        r.raise_for_status()
        data = r.json()
        last_total = int(data.get("total") or 0)
        for item in data.get("items") or []:
            tos = item.get("To") or []
            matched = any(
                (t.get("Mailbox") or "").lower() == mailbox.lower()
                and (t.get("Domain") or "").lower() == domain.lower()
                for t in tos
                if isinstance(t, dict)
            )
            if not matched:
                continue
            code = _extract_otp_from_mailhog_item(item)
            if code:
                return code
        time.sleep(0.5)
    raise AssertionError(
        f"OTP-письмо для {email_addr} не пришло в MailHog за {timeout_sec}s "
        f"(total messages={last_total})"
    )


def _psql(compose_file: Path, database: str, sql: str) -> str:
    r = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "cityvibe",
            "-d",
            database,
            "-At",
            "-F",
            "|",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if r.returncode != 0:
        raise AssertionError(f"psql failed: {r.stderr or r.stdout}")
    return (r.stdout or "").strip()


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

    with httpx.Client(base_url=gateway, timeout=30.0) as client:
        cities = _get_json(client, "/cities")
        assert isinstance(cities, list) and cities, "GET /cities должен вернуть города"
        city_id = int(cities[0]["id"])
        assert city_id > 0

        # Идентификатор ещё не занят
        existing = _psql(
            compose,
            "cityvibe_auth",
            f"SELECT count(*) FROM identities WHERE type='email' AND value='{email_addr}';",
        )
        assert existing == "0", f"email уже есть в auth DB: {email_addr}"

        challenge = _post_json(
            client,
            "/auth/register",
            {
                "name": name,
                "identifier": email_addr,
                "password": password,
                "city_id": city_id,
                "accept_terms": True,
                "birthdate": birthdate,
            },
        )
        assert challenge.get("channel") == "email"
        assert challenge.get("challenge_id")
        assert challenge.get("expires_in", 0) > 0

        # Pending-аккаунт до verify
        pending = _psql(
            compose,
            "cityvibe_auth",
            "SELECT a.id, a.status, a.name, a.city_id, a.birthdate, a.accept_terms "
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

        otp = _wait_otp_from_mailhog(mailhog, email_addr)
        assert re.fullmatch(r"\d{6}", otp), "OTP должен быть 6 цифр"

        tokens = _post_json(
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

        # Аккаунт активирован и привязан к user_id
        active = _psql(
            compose,
            "cityvibe_auth",
            f"SELECT status, user_id FROM accounts WHERE id={account_id};",
        )
        status, linked_user = active.split("|")
        assert status == "active"
        assert int(linked_user) == user_id

        verified = _psql(
            compose,
            "cityvibe_auth",
            f"SELECT verified FROM identities WHERE account_id={account_id} AND type='email';",
        )
        assert verified in {"t", "true", "1"}

        user = _get_json(client, f"/users/{user_id}")
        assert isinstance(user, dict)
        assert int(user["id"]) == user_id
        assert user["name"] == name
        assert user.get("deleted") is False
        assert user.get("onboarding_completed") is False
        assert int(user["city_id"]) == city_id
        assert str(user["birthdate"])[:10] == birthdate
        assert int(user["auth_account_id"]) == account_id

        # Source of truth в БД — профиль заполнен верно
        db_user = _psql(
            compose,
            "cityvibe_users",
            "SELECT name, city_id, birthdate, auth_account_id, deleted, onboarding_completed "
            f"FROM users WHERE id={user_id};",
        )
        assert db_user, f"user id={user_id} не найден в cityvibe_users"
        uname, ucity, ubirth, uauth, udeleted, uonb = db_user.split("|")
        assert uname == name
        assert int(ucity) == city_id
        assert ubirth == birthdate
        assert int(uauth) == account_id
        assert udeleted in {"f", "false", "0"}
        assert uonb in {"f", "false", "0"}

        # Повторная регистрация тем же email должна падать
        r = client.post(
            "/auth/register",
            json={
                "name": "Dup",
                "identifier": email_addr,
                "password": password,
                "city_id": city_id,
                "accept_terms": True,
            },
        )
        dup = r.json()
        assert r.status_code >= 400 or "error" in dup
        msg = _api_error_message(dup).lower()
        assert "существует" in msg or "already" in msg
