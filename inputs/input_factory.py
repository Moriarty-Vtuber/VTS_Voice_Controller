from core.event_bus import EventBus
from core.interfaces import ASRProcessor
from inputs.asr_processor import SherpaOnnxASRProcessor
from inputs.test_input_processor import TestInputProcessor
from loguru import logger


class InputProcessorFactory:
    @staticmethod
    def create_processor(processor_type: str, event_bus: EventBus) -> ASRProcessor:
        """
        Factory method to create an instance of an ASRProcessor.
        """
        logger.info(f"Creating input processor of type: {processor_type}")
        if processor_type == "test":
            return TestInputProcessor(event_bus)
        elif processor_type == "voice":
            return SherpaOnnxASRProcessor(event_bus)
        else:
            logger.error(f"Unknown input processor type: {processor_type}")
            raise ValueError(f"Unknown input processor type: {processor_type}")
