"""Тесты рендера Jinja2 email-шаблонов."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "notification_service"
    / "templates"
)


def _env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def test_otp_email_template_renders_code():
    html = _env().get_template("otp_email.html").render(code="654321", purpose="Регистрация")
    assert "654321" in html
    assert "Регистрация" in html


def test_welcome_email_template_renders_name():
    html = _env().get_template("welcome_email.html").render(name="Анна")
    assert "Анна" in html
