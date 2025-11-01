import asyncio
from loguru import logger
import os
import sys

from core.event_bus import EventBus
from core.vts_service import VTubeStudioService
from core.expression_service import ExpressionService
from core.intent_resolver import KeywordIntentResolver
from core.interfaces import ASRProcessor
from core.config_loader import ConfigLoader
from inputs.input_factory import InputProcessorFactory


class ApplicationCore:
    def __init__(self, config_path: str, test_mode: bool = False):
        self.config_path = config_path
        self.test_mode = test_mode
        self.recognition_mode = "fast"
        self.language = "en"
        self.event_bus = EventBus()
        self.config = ConfigLoader.load_yaml(config_path)
        self.models_config = self._load_models_config()
        self.vts_service = None
        self.expression_service = None
        self.intent_resolver = None
        self.input_processor: ASRProcessor = None
        self.selected_microphone_name = self.config.get(
            'vts_settings', {}).get('selected_microphone_name', 'Default')

    def _load_models_config(self):
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_config_path = os.path.join(
                base_path, 'config', 'models.yaml')
            return ConfigLoader.load_yaml(models_config_path)
        except Exception as e:
            logger.error(f"Failed to load models.yaml: {e}")
            return None

    async def _initialize_services(self):
        vts_settings = self.config.get('vts_settings', {})
        self.vts_service = VTubeStudioService(
            host=vts_settings.get('vts_host', 'localhost'),
            port=vts_settings.get('vts_port', 8001),
            token_file=vts_settings.get('token_file'),
            event_bus=self.event_bus
        )
        await self.vts_service.connect()
        await self.vts_service.authenticate()

        self.expression_service = ExpressionService(
            self.vts_service, self.config_path)
        expression_map = await self.expression_service.synchronize_and_get_map()
        self.intent_resolver = KeywordIntentResolver(
            self.event_bus, expression_map)

    async def _initialize_asr_processor(self):
        processor_type = "test" if self.test_mode else "voice"
        self.input_processor = InputProcessorFactory.create_processor(
            processor_type, self.event_bus)

        init_params = {"language": self.language}
        if processor_type == "voice":
            selected_model_config = self.models_config.get(
                self.language.lower())
            if not selected_model_config:
                logger.error(
                    f"Language '{self.language}' not supported in models.yaml.")
                return

            base_path = os.path.dirname(sys.executable) if getattr(
                sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_base_dir = os.path.join(base_path, "models")
            init_params.update({
                "config": selected_model_config,
                "model_url": selected_model_config.get("url"),
                "model_base_dir": model_base_dir,
                "microphone_name": self.selected_microphone_name
            })
        await self.input_processor.initialize(**init_params)

    async def run(self):
        await self._initialize_services()
        await self._initialize_asr_processor()

        if not all([self.input_processor, self.intent_resolver, self.vts_service]):
            logger.error("Core components failed to initialize. Aborting run.")
            return

        tasks = [
            asyncio.create_task(self.intent_resolver.resolve_intent()),
            asyncio.create_task(self._input_consumer()),
            asyncio.create_task(self._handle_hotkey_events()),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Application tasks cancelled.")
        finally:
            if self.vts_service:
                await self.vts_service.disconnect()
            if self.input_processor:
                await self.input_processor.stop_listening()

    async def _handle_hotkey_events(self):
        hotkey_queue = await self.event_bus.subscribe("hotkey_triggered")
        while True:
            event = await hotkey_queue.get()
            await self.vts_service.trigger_hotkey(event.payload)
            hotkey_queue.task_done()

    async def _input_consumer(self):
        try:
            async for _ in self.input_processor.start_listening():
                pass
        except asyncio.CancelledError:
            logger.info("Input consumer task cancelled.")

    async def initialize_expression_service(self):
        """Public method for UI to trigger expression sync."""
        if not self.vts_service:
            vts_settings = self.config.get('vts_settings', {})
            self.vts_service = VTubeStudioService(host=vts_settings.get('vts_host'), port=vts_settings.get(
                'vts_port'), token_file=vts_settings.get('token_file'), event_bus=self.event_bus)
            await self.vts_service.connect()
            await self.vts_service.authenticate()

        if not self.expression_service:
            self.expression_service = ExpressionService(
                self.vts_service, self.config_path)

        await self.expression_service.synchronize_and_get_map()
