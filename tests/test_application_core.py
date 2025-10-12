
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock the sounddevice module to prevent PortAudio error on import
sys.modules['sounddevice'] = MagicMock()

from core.application_core import ApplicationCore

class TestApplicationCore(unittest.TestCase):

    @patch('core.application_core.ASRProcessor', MagicMock())
    @patch('core.application_core.VTSWebSocketAgent')
    def test_application_run(self, mock_vts_agent):
        async def run_test():
            # Setup application
            app = ApplicationCore("vts_config.yaml", test_mode=True)

            # Mock the VTS agent methods
            mock_vts_agent_instance = AsyncMock()
            mock_vts_agent.return_value = mock_vts_agent_instance
            mock_vts_agent_instance.get_hotkey_list.return_value = {
                'data': {
                    'availableHotkeys': [
                        {
                            'name': 'test_expression',
                            'type': 'ToggleExpression',
                            'file': 'test.exp3.json',
                            'hotkeyID': 'hotkey_1'
                        }
                    ]
                }
            }

            # Run the app in a background task
            app_task = asyncio.create_task(app.run())

            # Get the queue for the hotkey_triggered event
            hotkey_queue = await app.event_bus.subscribe("hotkey_triggered")

            # Wait for the app to be ready
            await asyncio.sleep(1)

            # Publish a transcription event
            await app.event_bus.publish("transcription_received", "test_expression")

            # Wait for the event to be processed
            event = await hotkey_queue.get()

            # Check if hotkey is triggered
            self.assertEqual(event.payload, 'hotkey_1')

            # Clean up
            app_task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await app_task

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
