
import asyncio
from dataclasses import dataclass, field
from typing import Any
from loguru import logger


@dataclass
class Event:
    event_type: str
    payload: Any = field(default=None)


class EventBus:
    def __init__(self):
        self._queues = {}

    def get_queue(self, event_type: str) -> asyncio.Queue:
        if event_type not in self._queues:
            self._queues[event_type] = asyncio.Queue()
        return self._queues[event_type]

    async def publish(self, event_type: str, payload: Any):
        logger.debug(
            f"Publishing event '{event_type}' with payload: {payload}")
        event = Event(event_type=event_type, payload=payload)
        if event_type in self._queues:
            await self._queues[event_type].put(event)

    async def subscribe(self, event_type: str) -> asyncio.Queue:
        return self.get_queue(event_type)
