"""milana-agent лог: dict остаётся в JSON, строка msg — нет."""

import json
import logging
from io import StringIO

from src.mybootstrap_core_itskovichanton.logger import SimpleJsonFormatter

from python.milana_service.src.milana_service.infra.agent_log import log_agent


def test_log_agent_keeps_event_fields():
    logger = logging.getLogger("test-milana-agent-dict")
    logger.handlers.clear()
    logger.propagate = False
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SimpleJsonFormatter("%(t)s %(msg)s", trim_values_len=0))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    log_agent(logger, "deepseek_request", phase="catalog_match", user="фоткаться")
    payload = json.loads(stream.getvalue().strip())
    assert payload["event"] == "deepseek_request"
    assert payload["phase"] == "catalog_match"
    assert payload["user"] == "фоткаться"


def test_json_dumps_string_is_stripped_by_formatter():
    logger = logging.getLogger("test-milana-agent-str")
    logger.handlers.clear()
    logger.propagate = False
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SimpleJsonFormatter("%(t)s %(msg)s", trim_values_len=0))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info(json.dumps({"event": "deepseek_request", "user": "фоткаться"}))
    payload = json.loads(stream.getvalue().strip())
    assert "event" not in payload
    assert "user" not in payload
