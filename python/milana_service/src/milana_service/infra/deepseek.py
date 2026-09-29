"""DeepSeek Chat Completions (OpenAI-compatible) + файловый лог."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import httpx
from src.mybootstrap_core_itskovichanton.logger import LoggerService
from src.mybootstrap_ioc_itskovichanton.ioc import bean
from src.mybootstrap_mvc_itskovichanton.exceptions import CoreException

from python.libs.infra.envfile import load_repo_env
from python.milana_service.src.milana_service.infra.agent_log import log_agent


@bean(
    base_url=("deepseek.base_url", str, "https://api.deepseek.com"),
    model=("deepseek.model", str, "deepseek-chat"),
    max_tokens=("deepseek.max_tokens", int, 4096),
    temperature=("deepseek.temperature", float, 0.2),
    timeout_sec=("deepseek.timeout_sec", int, 90),
)
class DeepSeekClient:
    """Клиент DeepSeek. API key только из ENV DEEPSEEK_API_KEY."""

    logger_service: LoggerService

    def init(self, **kwargs):
        load_repo_env()
        self.base_url = (
            os.environ.get("DEEPSEEK_BASE_URL")
            or kwargs.get("base_url")
            or "https://api.deepseek.com"
        ).rstrip("/")
        self.model = os.environ.get("DEEPSEEK_MODEL") or kwargs.get("model") or "deepseek-chat"
        env_tok = os.environ.get("DEEPSEEK_MAX_TOKENS")
        self.max_tokens = int(env_tok) if env_tok else int(kwargs.get("max_tokens") or 4096)
        self.temperature = float(kwargs.get("temperature") or 0.2)
        self.timeout_sec = int(kwargs.get("timeout_sec") or 90)
        self.api_key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
        self._flog = self.logger_service.get_file_logger("milana-agent", max_line_len=0)
        log_agent(
            self._flog,
            "deepseek_init",
            configured=self.configured,
            model=self.model,
            base_url=self.base_url,
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _log(self, event: str, **payload: Any) -> None:
        log_agent(self._flog, event, **payload)

    async def chat_json(
        self,
        *,
        phase: str,
        system: str,
        user: str,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise CoreException(message="DEEPSEEK_API_KEY не задан")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"
        self._log(
            "deepseek_request",
            phase=phase,
            url=url,
            model=self.model,
            system=system,
            user=user,
            max_tokens=payload["max_tokens"],
        )
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code >= 400:
                self._log(
                    "deepseek_error",
                    phase=phase,
                    status=resp.status_code,
                    body=resp.text[:2000],
                )
                raise CoreException(
                    message=f"DeepSeek HTTP {resp.status_code}: {resp.text[:300]}",
                )
            data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")
        except (KeyError, IndexError, TypeError) as e:
            self._log("deepseek_bad_response", phase=phase, data=data)
            raise CoreException(message=f"Неожиданный ответ DeepSeek: {data!r}") from e
        self._log(
            "deepseek_response",
            phase=phase,
            usage=usage,
            content=content,
        )
        return _parse_json_content(content)


def _parse_json_content(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise CoreException(message=f"DeepSeek вернул не-JSON: {text[:400]}") from e
    if not isinstance(obj, dict):
        raise CoreException(message="DeepSeek JSON должен быть объектом")
    return obj
