import asyncio
from core.event_bus import EventBus

class MockVTubeStudioService:
    """Mock service for VTube Studio to be used in tests."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.connected = False
        self.authenticated = False
        self.hotkeys = []

    async def connect(self):
        self.connected = True
        await self.event_bus.publish("vts_status_update", "Connected")

    async def authenticate(self):
        if self.connected:
            self.authenticated = True
            await self.event_bus.publish("vts_status_update", "Authenticated")
        else:
            raise ConnectionError("Not connected to VTube Studio")

    async def trigger_hotkey(self, hotkey_id: str):
        if self.authenticated:
            await self.event_bus.publish("hotkey_triggered", hotkey_id)
        else:
            raise ConnectionError("Not authenticated with VTube Studio")

    async def get_hotkey_list(self):
        if self.authenticated:
            return {"data": {"availableHotkeys": self.hotkeys}}
        else:
            raise ConnectionError("Not authenticated with VTube Studio")

    async def disconnect(self):
        self.connected = False
        self.authenticated = False
        await self.event_bus.publish("vts_status_update", "Disconnected")
