from typing import AsyncIterator, Protocol


class EventBus(Protocol):
    async def publish(self, topic: str, message: bytes) -> None:
        """Отправка сообщения в шину (Exchange)"""
        ...

    def subscribe(self, topic: str, queue_name: str) -> AsyncIterator[bytes]:
        """
        Подписка на топик. Возвращает асинхронный генератор сообщений.
        Обратите внимание: сам метод теперь НЕ async, он просто возвращает объект итератора.
        """
        ...
