
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class InputProcessor(ABC):
    pass # No longer requires process_input

class ASRProcessor(InputProcessor):
    @abstractmethod
    async def initialize(self, config: dict, language: str):
        pass

    @abstractmethod
    async def start_listening(self) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def stop_listening(self):
        pass

    @abstractmethod
    async def get_transcription(self) -> str:
        pass

class IntentResolver(ABC):
    @abstractmethod
    async def resolve_intent(self):
        pass

class VTSOutputAgent(ABC):
    @abstractmethod
    async def trigger_hotkey(self, hotkey_id: str):
        pass
