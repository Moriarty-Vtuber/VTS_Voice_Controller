
import asyncio
import unittest
from core.event_bus import EventBus, Event

class TestEventBus(unittest.TestCase):

    def test_publish_subscribe(self):
        async def run_test():
            event_bus = EventBus()
            queue = await event_bus.subscribe("test_event")
            await event_bus.publish("test_event", "test_payload")
            event = await queue.get()
            self.assertEqual(event.event_type, "test_event")
            self.assertEqual(event.payload, "test_payload")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
