
from abc import ABC, abstractmethod

class InputProcessor(ABC):
    @abstractmethod
    async def process_input(self):
        pass

class IntentResolver(ABC):
    @abstractmethod
    async def resolve_intent(self):
        pass

class VTSOutputAgent(ABC):
    @abstractmethod
    async def trigger_hotkey(self, hotkey_id: str):
        pass
