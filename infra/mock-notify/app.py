"""Минимальный mock SMS/email gateway для локальной разработки."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mock-notify")

app = FastAPI(title="City Vibe Mock Notify Gateway", version="1.0.0")


class SmsIn(BaseModel):
    to: str = Field(..., description="E.164")
    text: str


class EmailIn(BaseModel):
    to: str
    subject: str
    html: str = ""
    text: str = ""


def _ok(result: dict) -> dict:
    return {"result": result}


def _err(message: str, *, status: int = 400, code: str = "bad_request") -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"message": message, "code": code}})


@app.get("/health")
async def health():
    return _ok({"status": "ok", "service": "mock-notify-gateway"})


@app.post("/sms")
async def send_sms(body: SmsIn):
    if not body.to.strip():
        return _err("Поле to обязательно")
    if not body.text.strip():
        return _err("Поле text обязательно")
    logger.info("SMS → %s | %s", body.to, body.text)
    return _ok(
        {
            "ok": True,
            "channel": "sms",
            "to": body.to,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.post("/email")
async def send_email(body: EmailIn):
    if not body.to.strip():
        return _err("Поле to обязательно")
    if not body.subject.strip():
        return _err("Поле subject обязательно")
    logger.info("EMAIL → %s | %s | html_len=%s", body.to, body.subject, len(body.html or ""))
    return _ok(
        {
            "ok": True,
            "channel": "email",
            "to": body.to,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
