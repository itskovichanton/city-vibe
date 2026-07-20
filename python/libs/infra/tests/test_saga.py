"""Тесты saga: компенсация при ошибке."""

import pytest

from python.libs.infra.saga import SagaContext, saga, saga_step


class DummyService:
    def __init__(self):
        self.created: list[int] = []
        self.deleted: list[int] = []

    async def create(self, n: int) -> int:
        self.created.append(n)
        return n

    async def delete(self, n: int) -> None:
        self.deleted.append(n)


async def compensate_created(user_id: int, self, n: int, **kwargs):
    await self.delete(user_id)


class Flow:
    def __init__(self):
        self.svc = DummyService()

    async def delete(self, user_id: int):
        await self.svc.delete(user_id)

    @saga("test.flow")
    async def execute(self, n: int, saga_ctx: SagaContext | None = None) -> int:
        user_id = await self._step_create(n, saga_ctx=saga_ctx)
        return await self._step_maybe_fail(user_id, n)

    @saga_step(compensate=compensate_created)
    async def _step_create(self, n: int, saga_ctx: SagaContext | None = None) -> int:
        return await self.svc.create(n)

    async def _step_maybe_fail(self, user_id: int, n: int) -> int:
        if n < 0:
            raise RuntimeError("fail after create")
        return user_id


@pytest.mark.asyncio
async def test_saga_compensates_on_failure():
    flow = Flow()
    with pytest.raises(RuntimeError):
        await flow.execute(-1)
    assert flow.svc.created == [-1]
    assert flow.svc.deleted == [-1]


@pytest.mark.asyncio
async def test_saga_success_no_compensation():
    flow = Flow()
    result = await flow.execute(42)
    assert result == 42
    assert flow.svc.created == [42]
    assert flow.svc.deleted == []
