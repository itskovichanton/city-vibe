"""DTO mock-notify gateway."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SmsIn:
    to: str
    text: str


@dataclass
class EmailIn:
    to: str
    subject: str
    html: str = ""
    text: str = ""
