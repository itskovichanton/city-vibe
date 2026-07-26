"""Общие хелперы для e2e против api-gateway + MailHog + Redis + Postgres."""

from __future__ import annotations

import base64
import email
import json
import re
import subprocess
import time
import uuid
from email import policy
from pathlib import Path

import httpx
import pytest

# 1×1 PNG — валидный image/png для filetype
MIN_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

DEFAULT_PASSWORD = "SecurePass1!"
MIN_ATTR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "has_wifi": {"type": "boolean"},
        "price_level": {"type": "integer", "minimum": 1, "maximum": 4},
    },
}


def unwrap(payload: dict | list) -> dict | list:
    if isinstance(payload, dict) and "result" in payload:
        return payload["result"]
    return payload


def api_error_message(payload: dict) -> str:
    err = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(err, dict):
        return str(err.get("message") or err)
    return str(payload)


def post_json(client: httpx.Client, path: str, body: dict, *, expect_ok: bool = True) -> dict:
    r = client.post(path, json=body)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON body: {r.text[:300]}")
    if expect_ok and (r.status_code >= 400 or (isinstance(data, dict) and "error" in data)):
        pytest.fail(f"{path}: HTTP {r.status_code}: {api_error_message(data)}")
    out = unwrap(data) if expect_ok else data
    if expect_ok:
        assert isinstance(out, dict), f"{path}: ожидался object, получили {type(out)}"
        return out
    assert isinstance(data, dict)
    return data


def put_json(client: httpx.Client, path: str, body: dict) -> dict:
    r = client.put(path, json=body)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON body: {r.text[:300]}")
    if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
        pytest.fail(f"{path}: HTTP {r.status_code}: {api_error_message(data)}")
    out = unwrap(data)
    assert isinstance(out, dict), f"{path}: ожидался object, получили {type(out)}"
    return out


def patch_json(client: httpx.Client, path: str, body: dict) -> dict:
    r = client.patch(path, json=body)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON body: {r.text[:300]}")
    if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
        pytest.fail(f"{path}: HTTP {r.status_code}: {api_error_message(data)}")
    out = unwrap(data)
    assert isinstance(out, dict), f"{path}: ожидался object, получили {type(out)}"
    return out


def delete_json(client: httpx.Client, path: str) -> dict:
    r = client.delete(path)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON body: {r.text[:300]}")
    if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
        pytest.fail(f"{path}: HTTP {r.status_code}: {api_error_message(data)}")
    out = unwrap(data)
    assert isinstance(out, dict), f"{path}: ожидался object, получили {type(out)}"
    return out


def get_json(client: httpx.Client, path: str) -> dict | list:
    r = client.get(path)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON body: {r.text[:300]}")
    if r.status_code >= 400 or (isinstance(data, dict) and "error" in data):
        pytest.fail(f"{path}: HTTP {r.status_code}: {api_error_message(data)}")
    return unwrap(data)


def extract_otp_from_mailhog_item(item: dict) -> str | None:
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
        m = re.search(r"(?:код|code)\s*[:=]?\s*(\d{6})", text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"(?<!\d)(\d{6})(?!\d)", text)
        if m:
            return m.group(1)
    return None


def wait_otp_from_mailhog(mailhog: str, email_addr: str, timeout_sec: float = 30.0) -> str:
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
            code = extract_otp_from_mailhog_item(item)
            if code:
                return code
        time.sleep(0.5)
    raise AssertionError(
        f"OTP-письмо для {email_addr} не пришло в MailHog за {timeout_sec}s "
        f"(total messages={last_total})"
    )


def otp_from_redis(challenge_id: str, timeout_sec: float = 10.0) -> str:
    """Читает код OTP из Redis, куда пишет auth-service (обычно localhost:6379)."""
    key = f"cityvibe:otp:{challenge_id}"
    deadline = time.time() + timeout_sec

    def _read_once() -> str | None:
        # 1) host redis-cli — auth использует CITYVIBE_REDIS_URL / localhost:6379
        for cmd in (
            ["redis-cli", "-u", "redis://127.0.0.1:6379/0", "GET", key],
            ["redis-cli", "-h", "127.0.0.1", "-p", "6379", "-n", "0", "GET", key],
            ["docker", "exec", "cityvibe-redis", "redis-cli", "GET", key],
        ):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            except FileNotFoundError:
                continue
            raw = (r.stdout or "").strip()
            if r.returncode == 0 and raw and raw != "(nil)":
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                code = str(data.get("code") or "")
                if re.fullmatch(r"\d{6}", code):
                    return code
        # 2) redis-py fallback
        try:
            import redis as redis_sync

            client = redis_sync.Redis.from_url("redis://127.0.0.1:6379/0", decode_responses=True)
            try:
                raw = client.get(key)
            finally:
                client.close()
            if raw:
                data = json.loads(raw)
                code = str(data.get("code") or "")
                if re.fullmatch(r"\d{6}", code):
                    return code
        except Exception:
            pass
        return None

    while time.time() < deadline:
        code = _read_once()
        if code:
            return code
        time.sleep(0.2)
    raise AssertionError(f"OTP challenge {challenge_id} не найден в Redis")


def wait_otp(
    *,
    mailhog: str | None,
    email_addr: str | None,
    challenge_id: str,
    channel: str | None = None,
) -> str:
    """
    Код для конкретного challenge_id.
    Сначала Redis (источник правды), MailHog — только fallback для email-доставки.
    Иначе на одном ящике легко поймать OTP от register вместо login/resend.
    """
    try:
        return otp_from_redis(challenge_id, timeout_sec=8.0)
    except AssertionError:
        if channel == "sms" or not email_addr or not mailhog:
            raise
        return wait_otp_from_mailhog(mailhog, email_addr)


def psql(compose_file: Path, database: str, sql: str) -> str:
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


def unique_email(prefix: str = "e2e") -> str:
    return f"{prefix}.{uuid.uuid4().hex[:12]}@example.com"


def unique_phone() -> str:
    """Уникальный валидный RU мобильный (+7900XXXXXXX)."""
    suffix = int(uuid.uuid4().hex[:7], 16) % 10_000_000
    return f"+7900{suffix:07d}"


def first_city_id(client: httpx.Client) -> int:
    cities = get_json(client, "/cities")
    assert isinstance(cities, list) and cities, "GET /cities должен вернуть города"
    city_id = int(cities[0]["id"])
    assert city_id > 0
    return city_id


def register_and_verify(
    client: httpx.Client,
    *,
    mailhog: str,
    identifier: str | None = None,
    password: str = DEFAULT_PASSWORD,
    name: str | None = None,
    gender: str = "male",
    birthdate: str = "1995-04-12",
    city_id: int | None = None,
) -> dict:
    """Полный register → OTP → verify. Возвращает TokensOut + meta."""
    email_addr = identifier or unique_email("e2e.user")
    city_id = city_id or first_city_id(client)
    display = name or f"E2E {uuid.uuid4().hex[:8]}"
    challenge = post_json(
        client,
        "/auth/register",
        {
            "name": display,
            "identifier": email_addr,
            "password": password,
            "city_id": city_id,
            "accept_terms": True,
            "birthdate": birthdate,
            "gender": gender,
        },
    )
    otp = wait_otp(
        mailhog=mailhog,
        email_addr=email_addr if "@" in email_addr else None,
        challenge_id=challenge["challenge_id"],
        channel=challenge.get("channel"),
    )
    tokens = post_json(
        client,
        "/auth/register/verify",
        {"challenge_id": challenge["challenge_id"], "code": otp},
    )
    return {
        "tokens": tokens,
        "identifier": email_addr,
        "password": password,
        "name": display,
        "city_id": city_id,
        "gender": gender,
        "user_id": int(tokens["user_id"]),
        "account_id": int(tokens["account_id"]),
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


def ensure_attr_schema(compose_file: Path, category_code: str = "bars") -> None:
    schema_json = json.dumps(MIN_ATTR_SCHEMA, ensure_ascii=False).replace("'", "''")
    sql = (
        "INSERT INTO attr_schemas (category_code, version, json_schema, deleted) "
        f"VALUES ('{category_code}', 1, '{schema_json}'::jsonb, FALSE) "
        "ON CONFLICT (category_code) DO UPDATE SET "
        "json_schema = EXCLUDED.json_schema, deleted = FALSE, updated_at = NOW();"
    )
    psql(compose_file, "cityvibe_places", sql)


def assert_http_error(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    r = getattr(client, method.lower())(path, **kwargs)
    try:
        data = r.json()
    except Exception:
        pytest.fail(f"{path}: HTTP {r.status_code}, non-JSON: {r.text[:300]}")
    assert r.status_code >= 400 or (isinstance(data, dict) and "error" in data), (
        f"{path}: ожидалась ошибка, получили HTTP {r.status_code}: {data}"
    )
    assert isinstance(data, dict)
    return data
