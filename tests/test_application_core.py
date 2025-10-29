import asyncio
import pytest
import sys
from unittest.mock import MagicMock, AsyncMock

# Mock modules with missing system dependencies
sys.modules['sounddevice'] = MagicMock()

from core.application_core import ApplicationCore
from tests.mocks.mock_vts_service import MockVTubeStudioService
from core.event_bus import EventBus

@pytest.fixture
def event_bus():
    return EventBus()

@pytest.fixture
def mock_vts_service(event_bus):
    return MockVTubeStudioService(event_bus)

@pytest.fixture
def app_core(mock_vts_service, event_bus):
    # Create a dummy config file for testing
    with open("vts_config.yaml", "w") as f:
        f.write("""
vts_settings:
  vts_host: "localhost"
  vts_port: 8001
  token_file: "token.txt"
expressions:
  Expression1:
    name: "Test Expression"
    keywords: ["test"]
    cooldown_s: 10
        """)
    core = ApplicationCore(config_path="vts_config.yaml", test_mode=True)
    core.vts_service = mock_vts_service
    # Replace the original vts_service instance with the mock
    core._initialize_components = lambda: _mock_initialize_components(core, mock_vts_service)
    return core

async def _mock_initialize_components(app_core, mock_vts_service):
    app_core.vts_service = mock_vts_service
    await app_core.vts_service.connect()
    await app_core.vts_service.authenticate()
    # Since we are mocking the entire method, we need to manually set the return values
    app_core.intent_resolver = AsyncMock()
    # Make the input_processor a long-running async generator
    async def mock_start_listening():
        while True:
            await asyncio.sleep(1)
            yield "test"
    app_core.input_processor = AsyncMock()
    app_core.input_processor.start_listening = mock_start_listening
    app_core.available_vts_expression_names = ["Test Expression"]
    return {}, ["Test Expression"]

@pytest.mark.asyncio
async def test_application_core_initialization(app_core):
    assert app_core is not None
    assert app_core.vts_service is not None
    assert isinstance(app_core.vts_service, MockVTubeStudioService)

@pytest.mark.asyncio
async def test_run_initializes_components_and_starts_listeners(app_core, mock_vts_service):
    # Mock the hotkey list to be returned by the service
    mock_vts_service.hotkeys = [
        {"file": "Expression1", "name": "Test Expression", "hotkeyID": "hotkey1", "type": "ToggleExpression"}
    ]

    run_task = asyncio.create_task(app_core.run())
    await asyncio.sleep(0.1) # Give some time for the run loop to start

    # Assert that the service was connected and authenticated
    assert mock_vts_service.connected
    assert mock_vts_service.authenticated

    # Assert that the intent resolver was created
    assert app_core.intent_resolver is not None

    # Assert that the test input processor was initialized
    assert app_core.input_processor is not None

    run_task.cancel()
    try:
        await run_task
    except asyncio.CancelledError:
        pass
