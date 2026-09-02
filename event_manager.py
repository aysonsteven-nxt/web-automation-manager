import asyncio
import json
from typing import Any

from sse_starlette.event import ServerSentEvent


class EventManager:
    def __init__(self) -> None:
        self.clients: set[asyncio.Queue[ServerSentEvent]] = set()

    async def connect(self) -> asyncio.Queue[ServerSentEvent]:
        queue: asyncio.Queue[ServerSentEvent] = asyncio.Queue()
        self.clients.add(queue)

        return queue

    def disconnect(
        self,
        queue: asyncio.Queue[ServerSentEvent],
    ) -> None:
        self.clients.discard(queue)

    async def broadcast(
        self,
        event_type: str,
        data: Any,
    ) -> None:
        event = ServerSentEvent(
            event=event_type,
            data=json.dumps(data),
        )

        disconnected: list[
            asyncio.Queue[ServerSentEvent]
        ] = []

        for queue in self.clients:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                disconnected.append(queue)

        for queue in disconnected:
            self.disconnect(queue)


event_manager = EventManager()