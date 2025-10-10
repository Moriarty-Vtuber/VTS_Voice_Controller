
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from core.application_core import ApplicationCore

class TestApplicationCore(unittest.TestCase):

    @patch('core.application_core.ASRProcessor')
    @patch('core.application_core.VTSWebSocketAgent')
    def test_application_run(self, mock_vts_agent, mock_asr_processor):
        async def run_test():
            # Setup application
            app = ApplicationCore("vts_config.yaml")

            # Mock the VTS agent methods
            mock_vts_agent.return_value.connect = AsyncMock()
            mock_vts_agent.return_value.authenticate = AsyncMock()
            mock_vts_agent.return_value.get_hotkey_list.return_value = {
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

            # Run the app initialization
            await app._initialize_components()

            # Get the queue for the hotkey_triggered event
            hotkey_queue = await app.event_bus.subscribe("hotkey_triggered")

            # Directly process a transcription
            await app.intent_resolver._process_one_event("test_expression")

            # Wait for the event to be processed
            event = await hotkey_queue.get()

            # Check if hotkey is triggered
            self.assertEqual(event.payload, 'hotkey_1')


        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
