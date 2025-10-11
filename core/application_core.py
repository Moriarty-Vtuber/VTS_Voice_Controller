
import asyncio
import yaml
from loguru import logger
import os
import sys

from core.event_bus import EventBus
from agents.vts_output_agent import VTSWebSocketAgent
from core.intent_resolver import KeywordIntentResolver
from inputs.test_input_processor import TestInputProcessor
from inputs.asr_processor import ASRProcessor
from inputs.utils.utils import ensure_model_downloaded_and_extracted

class ApplicationCore:
    def __init__(self, config_path: str, test_mode: bool = False, recognition_mode: str = "fast", language: str = "en"):
        self.config_path = config_path
        self.test_mode = test_mode
        self.recognition_mode = recognition_mode
        self.event_bus = EventBus()
        self.config = self._load_config()
        self.models_config = self._load_models_config()
        self.vts_agent = None
        self.intent_resolver = None
        self.input_processor = None
        self.current_language = language

    def _load_config(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        config_path = os.path.join(base_path, self.config_path)

        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found at {config_path}. Creating a default one.")
            default_config = {
                'vts_settings': {
                    'host': '127.0.0.1',
                    'port': 8001,
                    'token_file': os.path.join(base_path, 'vts_token.txt')
                },
                'expressions': {
                    'DefaultExpression.exp3.json': {
                        'name': 'DefaultExpression',
                        'keywords': ['hello'],
                        'cooldown_s': 60
                    }
                }
            }
            try:
                with open(config_path, 'w') as f:
                    yaml.safe_dump(default_config, f, default_flow_style=False, allow_unicode=True)
                logger.info("Default configuration created.")
                return default_config
            except Exception as e:
                logger.error(f"Error creating default configuration: {e}")
                return None
        else:
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading configuration from {config_path}: {e}")
                return None

    def _load_models_config(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_config_path = os.path.join(base_path, 'config', 'models.yaml')
        try:
            with open(models_config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading models configuration from {models_config_path}: {e}")
            return None

    async def set_language(self, language: str):
        if not self.models_config:
            logger.error("Models configuration not loaded. Cannot switch language.")
            return

        self.current_language = language
        logger.info(f"Attempting to set ASR language to: {language}")

        selected_model = self.models_config.get(language.lower())
        if not selected_model:
            logger.error(f"Language '{language}' not supported in models.yaml. Please check the config.")
            return

        model_url = selected_model["url"]
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_base_dir = os.path.join(base_path, "models")
        
        try:
            actual_model_dir = ensure_model_downloaded_and_extracted(model_url, model_base_dir)
        except Exception as e:
            logger.error(f"Failed to prepare model for language {language}: {e}")
            return

        # Stop existing input processor if it's running
        if self.input_processor and hasattr(self.input_processor, 'stop'):
            await self.input_processor.stop()

        params = selected_model["params"]
        self.input_processor = ASRProcessor(
            event_bus=self.event_bus,
            tokens_path=os.path.join(actual_model_dir, params["tokens"]),
            encoder_path=os.path.join(actual_model_dir, params["encoder"]),
            decoder_path=os.path.join(actual_model_dir, params["decoder"]),
            joiner_path=os.path.join(actual_model_dir, params["joiner"]),
            provider="cpu", # Defaulting to CPU
            recognition_mode=self.recognition_mode,
        )
        logger.info(f"Successfully initialized ASR for language: {language}")

    async def _initialize_components(self):
        if not self.config:
            logger.error("Initialization failed: Configuration is not loaded.")
            return

        vts_settings = self.config['vts_settings']
        self.vts_agent = VTSWebSocketAgent(
            host=vts_settings['host'],
            port=vts_settings['port'],
            token_file=vts_settings['token_file'],
            event_bus=self.event_bus
        )

        await self.vts_agent.connect()
        await self.vts_agent.authenticate()

        expression_map = await self._synchronize_expressions() or {}

        self.intent_resolver = KeywordIntentResolver(self.event_bus, expression_map)

        if self.test_mode:
            logger.info("--- RUNNING IN TEST MODE ---")
            self.input_processor = TestInputProcessor(self.event_bus)
        else:
            logger.info("--- RUNNING IN NORMAL MODE (MICROPHONE INPUT) ---")
            await self.set_language(self.current_language) # Set default language

    async def run(self):
        await self._initialize_components()
        if not self.vts_agent or not self.intent_resolver:
            logger.error("Application cannot start due to initialization failure.")
            return

        # If no input processor is available (i.e., not in test mode and ASR is disabled), exit gracefully.
        if not self.input_processor:
            logger.error("No input processor available. The application will now exit.")
            logger.error("Run with the --test flag for testing, or resolve the onnxruntime issue to enable microphone input.")
            await self.vts_agent.disconnect()
            return

        logger.info("Starting application components...")
        
        tasks = [
            asyncio.create_task(self.intent_resolver.resolve_intent()),
            asyncio.create_task(self.vts_agent.run()),
            asyncio.create_task(self.input_processor.process_input()),
        ]

        # If in test mode, we need a way to stop the application
        if self.test_mode:
            async def test_shutdown_manager():
                await asyncio.sleep(10) # Give ample time for the test event to fire and be processed
                logger.warning("--- TEST COMPLETE: SHUTTING DOWN APPLICATION ---")
                for task in tasks:
                    task.cancel()
            tasks.append(asyncio.create_task(test_shutdown_manager()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Application tasks were cancelled.")
        except KeyboardInterrupt:
            logger.info("Stopping application...")
        finally:
            for task in asyncio.all_tasks():
                if task is not asyncio.current_task():
                    task.cancel()
            if self.vts_agent:
                await self.vts_agent.disconnect()

    async def _synchronize_expressions(self):
        logger.info("Checking for expression updates from VTube Studio...")
