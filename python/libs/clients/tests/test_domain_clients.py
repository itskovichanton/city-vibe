"""Unit-тесты domain HTTP clients (только DTO, без IoC)."""

from python.libs.clients.domain.auth_service.entities import RegisterBody, VerifyBody
from python.libs.clients.domain.mock_notify.entities import EmailIn, SmsIn
from python.libs.clients.domain.place_service.entities import CityOut, GeoOut
from python.libs.clients.domain.user_service.entities import CreateUserBody


def test_create_user_body_optional_fields():
    body = CreateUserBody(
        name="Test",
        city_id=1,
        birthdate="1990-01-15",
        auth_account_id=99,
    )
    assert body.city_id == 1
    assert body.birthdate == "1990-01-15"
    assert body.auth_account_id == 99


def test_auth_entities():
    reg = RegisterBody(
        name="Anna",
        identifier="a@test.com",
        password="Pass123!",
        city_id=1,
        accept_terms=True,
    )
    assert reg.name == "Anna"
    verify = VerifyBody(challenge_id="abc", code="123456")
    assert verify.code == "123456"


def test_place_service_entities():
    city = CityOut(
        id=1,
        name="Москва",
        slug="moskva",
        geo=GeoOut(latitude=55.75, longitude=37.62),
        created_at="2026-01-01T00:00:00Z",
    )
    assert city.geo.latitude == 55.75


def test_mock_notify_entities():
    sms = SmsIn(to="+79991234567", text="code 123456")
    email = EmailIn(to="a@test.com", subject="Hi", html="<b>Hi</b>")
    assert sms.text.startswith("code")
    assert email.subject == "Hi"
