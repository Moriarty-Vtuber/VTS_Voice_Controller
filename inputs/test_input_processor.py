import asyncio
from loguru import logger

from core.interfaces import InputProcessor
from core.event_bus import EventBus

class TestInputProcessor(InputProcessor):
    def __init__(self, event_bus: EventBus, test_phrase: str = "I am so angry"):
        self.event_bus = event_bus
        self.test_phrase = test_phrase

    async def process_input(self):
        """Waits for a few seconds, publishes a test phrase, and then stops."""
        await asyncio.sleep(5) # Wait for everything to settle
        logger.warning(f"--- SIMULATING VOICE COMMAND: '{self.test_phrase}' ---")
        await self.event_bus.publish("transcription_received", self.test_phrase)
        logger.warning("--- SIMULATION SENT ---")
        # This processor's job is done after one event.
        # The main application will handle shutdown.
