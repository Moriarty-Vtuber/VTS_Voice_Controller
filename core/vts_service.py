import asyncio
from loguru import logger
import pyvts
from core.event_bus import EventBus


class VTubeStudioService:
    """Service to interact with the VTube Studio API via WebSocket."""

    def __init__(self, host: str, port: int, token_file: str, event_bus: EventBus):
        self.host = host
        self.port = port
        self.token_file = token_file
        self.event_bus = event_bus
        self.vts = pyvts.vts(plugin_info={
            "plugin_name": "VTS Voice Controller",
            "developer": "Gemini",
            "authentication_token_path": self.token_file,
        })
        self.request_lock = asyncio.Lock()

    async def connect(self, max_retries=5, retry_delay=5):
        """Connect to VTube Studio with a retry mechanism."""
        await self.event_bus.publish("vts_status_update", "Connecting...")
        for attempt in range(max_retries):
            try:
                await self.vts.connect()
                logger.info("Connected to VTube Studio.")
                await self.event_bus.publish("vts_status_update", "Connected")
                return
            except Exception as e:
                logger.warning(
                    f"Connection attempt {attempt + 1} of {max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(
                        "Could not connect to VTube Studio after all retries.")
                    logger.error(
                        "Please ensure VTube Studio is running and the API is enabled on port 8001.")
                    await self.event_bus.publish("vts_status_update", "Connection Failed")
                    raise

    async def authenticate(self):
        """Authenticate with VTube Studio."""
        try:
            async with self.request_lock:
                await self.vts.request_authenticate_token()
                authenticated = await self.vts.request_authenticate()
            if authenticated:
                logger.info("Authenticated successfully with VTube Studio.")
                await self.event_bus.publish("vts_status_update", "Authenticated")
            else:
                logger.warning(
                    "Authentication failed. Please allow the plugin in VTube Studio.")
                await self.event_bus.publish("vts_status_update", "Authentication Failed")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self.event_bus.publish("vts_status_update", "Authentication Error")
            raise

    async def trigger_hotkey(self, hotkey_id: str):
        """Trigger a hotkey in VTube Studio."""
        request = self.vts.vts_request.requestTriggerHotKey(hotkey_id)
        try:
            response = await self.vts.request(request)
            if "hotkeyID" in response.get("data", {}):
                logger.info(f"Triggered hotkey: {hotkey_id}")
            else:
                logger.warning(
                    f"Failed to trigger hotkey {hotkey_id}. Response: {response}")
        except Exception as e:
            logger.error(f"Failed to trigger hotkey '{hotkey_id}': {e}")

    async def get_hotkey_list(self):
        """Get a list of all hotkeys for the current model."""
        logger.info("Requesting hotkey list from VTube Studio...")
        request = self.vts.vts_request.requestHotKeyList()
        try:
            async with self.request_lock:
                response = await self.vts.request(request)
            return response
        except Exception as e:
            logger.error(f"Failed to get hotkey list: {e}")
            raise

    async def disconnect(self):
        """Disconnect from VTube Studio."""
        if self.vts.get_connection_status() == 1:
            await self.vts.close()
            logger.info("Disconnected from VTube Studio.")
            await self.event_bus.publish("vts_status_update", "Disconnected")
