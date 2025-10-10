
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.vts_output_agent import VTSWebSocketAgent
from core.event_bus import Event, EventBus

class TestVTSOutputAgent(unittest.TestCase):

    @patch('pyvts.vts')
    def test_trigger_hotkey(self, mock_vts):
        async def run_test():
            event_bus = EventBus()
            mock_vts_instance = MagicMock()
            mock_vts_instance.request = AsyncMock(return_value={'data': {'hotkeyID': 'hotkey_1'}})
            mock_vts.return_value = mock_vts_instance

            agent = VTSWebSocketAgent("host", 1234, "token_file", event_bus)

            # Run the agent in a background task
            agent_task = asyncio.create_task(agent.run())

            # Publish a hotkey trigger event
            hotkey_queue = await event_bus.subscribe("hotkey_triggered")
            await event_bus.publish("hotkey_triggered", "hotkey_1")

            # Give the agent time to process
            await asyncio.sleep(0.1)

            # Check that the vts request was called
            mock_vts_instance.request.assert_called()

            agent_task.cancel()

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
