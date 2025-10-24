import asyncio
from loguru import logger
from typing import AsyncGenerator

from core.interfaces import ASRProcessor
from core.event_bus import EventBus

class TestInputProcessor(ASRProcessor):
    def __init__(self, event_bus: EventBus, test_phrase: str = "I am so angry"):
        self.event_bus = event_bus
        self.test_phrase = test_phrase
        self.running = False

    async def initialize(self, config: dict, language: str):
        logger.info("TestInputProcessor initialized.")
        await self.event_bus.publish("asr_status_update", "Test Mode Ready")

    async def start_listening(self) -> AsyncGenerator[str, None]:
        self.running = True
        logger.info("--- RUNNING IN TEST MODE ---")
        await self.event_bus.publish("asr_ready", True)
        await asyncio.sleep(2) # Simulate some startup time
        if self.running:
            logger.warning(f"--- SIMULATING VOICE COMMAND: '{self.test_phrase}' ---")
            await self.event_bus.publish("transcription_received", self.test_phrase)
            yield self.test_phrase # Yield the test phrase once
            logger.warning("--- SIMULATION SENT ---")
        self.running = False # Stop after yielding once

    async def stop_listening(self):
        self.running = False
        logger.info("TestInputProcessor stopped listening.")
        await self.event_bus.publish("asr_status_update", "Stopped")

    async def get_transcription(self) -> str:
        return "" # Not applicable for this test processor