import asyncio
from typing import Any


class EventManager:
    def __init__(self):
        self._queues: set[asyncio.Queue] = set()

    async def connect(self) -> asyncio.Queue:
        queue = asyncio.Queue()

        self._queues.add(queue)

        return queue

    def disconnect(
        self,
        queue: asyncio.Queue,
    ) -> None:
        self._queues.discard(queue)

    async def broadcast(
        self,
        event_name: str,
        data: Any,
    ) -> None:
        event = {
            "event": event_name,
            "data": data,
        }

        for queue in list(self._queues):
            await queue.put(event)


event_manager = EventManager()