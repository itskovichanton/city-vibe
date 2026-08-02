"""Патчи для mybootstrap ActionRunner (use-case без аргументов)."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


def callable_expects_pipeline_arg(fn: Callable[..., Any]) -> bool:
    """
    True, если callable ожидает positional-аргумент от ActionRunner (кроме bound self).

    ActionRunner передаёт `call` как первый positional аргумент action.
    Для `async def execute(self) -> T` аргумент не нужен — иначе TypeError.
    """
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return True

    params = [
        p
        for p in sig.parameters.values()
        if p.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
    ]
    if not params:
        return False
    if len(params) == 1 and params[0].default is not inspect.Parameter.empty:
        return False
    return True


def invoke_pipeline_callable(
    fn: Callable[..., Any],
    args: Any,
    *,
    unbox_call: bool = False,
) -> Any:
    """Вызов action из ActionRunner с учётом zero-arg use-case."""
    if unbox_call:
        return fn(**args)
    if args is None and not callable_expects_pipeline_arg(fn):
        return fn()
    return fn(args)


def patch_action_runner_callable() -> None:
    """Monkey-patch CallableAction.run (идемпотентно)."""
    from src.mybootstrap_mvc_itskovichanton import pipeline as mvc_pipeline

    if getattr(mvc_pipeline.CallableAction.run, "_cityvibe_patched", False):
        return

    original_run = mvc_pipeline.CallableAction.run

    def patched_run(self, args: Any = None) -> Any:
        return invoke_pipeline_callable(
            self.call,
            args,
            unbox_call=self.unbox_call,
        )

    patched_run._cityvibe_patched = True  # type: ignore[attr-defined]
    mvc_pipeline.CallableAction.run = patched_run  # type: ignore[method-assign]

    _ = original_run  # kept for debugging if needed
