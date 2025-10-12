
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from core.intent_resolver import KeywordIntentResolver
from core.event_bus import Event, EventBus

class TestIntentResolver(unittest.TestCase):

    def test_resolve_intent(self):
        async def run_test():
            event_bus = EventBus()
            expression_map = {
                "hello": {"hotkeyID": "hotkey_1", "cooldown_s": 10}
            }
            intent_resolver = KeywordIntentResolver(event_bus, expression_map)

            # Get the queue for the hotkey_triggered event
            hotkey_queue = await event_bus.subscribe("hotkey_triggered")

            # Run the resolver in a background task
            resolver_task = asyncio.create_task(intent_resolver.resolve_intent())

            # Publish a transcription event
            transcription_queue = await event_bus.subscribe("transcription_received")
            await event_bus.publish("transcription_received", "hello world")

            # Wait for the event to be processed
            event = await hotkey_queue.get()

            # Check that the correct hotkey was published
            self.assertEqual(event.payload, "hotkey_1")

            resolver_task.cancel()

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
