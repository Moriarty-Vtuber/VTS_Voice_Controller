from abc import ABC, abstractmethod
from typing import AsyncGenerator

class InputProcessor(ABC):
    @abstractmethod
    async def initialize(self, config: dict, language: str):
        pass

class ASRProcessor(InputProcessor):
    @abstractmethod
    async def start_listening(self) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def stop_listening(self):
        pass

class VTSOutputAgent(ABC):
    @abstractmethod
    async def trigger_hotkey(self, hotkey_id: str):
        pass

class VTSDataProcessor(ABC):
    @abstractmethod
    async def run(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

class IntentResolver(ABC):
    @abstractmethod
    async def resolve_intent(self):
        pass

class EmotionProcessor(ABC):
    @abstractmethod
    async def initialize(self, config: dict):
        pass

    @abstractmethod
    async def start_detection(self) -> AsyncGenerator[dict, None]:
        pass

    @abstractmethod
    async def stop_detection(self):
        pass

    @abstractmethod
    async def get_detected_emotion(self) -> str:
        pass
