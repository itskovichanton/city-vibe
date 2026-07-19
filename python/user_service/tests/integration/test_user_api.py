"""Заготовка интеграционных тестов (нужен поднятый postgres / rabbitmq)."""

import pytest


@pytest.mark.skip(reason="Требует make infra-up — подключим в следующих итерациях")
@pytest.mark.asyncio
async def test_create_user_integration():
    assert False
