"""Тесты патча ActionRunner для zero-arg use-case."""

from __future__ import annotations

import pytest

from python.libs.infra.pipeline import (
    callable_expects_pipeline_arg,
    invoke_pipeline_callable,
    patch_action_runner_callable,
)


class _Svc:
    async def execute(self) -> str:
        return "ok"

    async def execute_with_req(self, request: str) -> str:
        return request

    async def execute_optional(self, request: str | None = None) -> str:
        return request or "default"


@pytest.mark.parametrize(
    ("fn_name", "expects_arg"),
    [
        ("execute", False),
        ("execute_with_req", True),
        ("execute_optional", False),
    ],
)
def test_callable_expects_pipeline_arg(fn_name: str, expects_arg: bool) -> None:
    svc = _Svc()
    fn = getattr(svc, fn_name)
    assert callable_expects_pipeline_arg(fn) is expects_arg


def test_invoke_pipeline_callable_zero_arg() -> None:
    import asyncio

    svc = _Svc()
    coro = invoke_pipeline_callable(svc.execute, None)
    assert asyncio.iscoroutine(coro)
    assert asyncio.run(coro) == "ok"


def test_invoke_pipeline_callable_with_arg() -> None:
    import asyncio

    svc = _Svc()
    coro = invoke_pipeline_callable(svc.execute_with_req, "city")
    assert asyncio.run(coro) == "city"


def test_patch_action_runner_callable_idempotent() -> None:
    from src.mybootstrap_mvc_itskovichanton import pipeline as mvc_pipeline

    patch_action_runner_callable()
    first = mvc_pipeline.CallableAction.run
    patch_action_runner_callable()
    assert mvc_pipeline.CallableAction.run is first

    action = mvc_pipeline.CallableAction(call=_Svc().execute)
    import asyncio

    assert asyncio.run(action.run(None)) == "ok"
