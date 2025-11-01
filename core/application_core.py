import asyncio
import yaml
from loguru import logger
import os
import sys

from core.event_bus import EventBus
from core.vts_service import VTubeStudioService
from core.intent_resolver import KeywordIntentResolver
from inputs.test_input_processor import TestInputProcessor
from inputs.asr_processor import SherpaOnnxASRProcessor
from inputs.emotion_detector import CnnEmotionDetector
from core.interfaces import ASRProcessor, EmotionProcessor
from core.config_loader import ConfigLoader

EMOTION_COOLDOWN_SECONDS = 5 # Cooldown for emotion-triggered expressions

class ApplicationCore:
    def __init__(self, config_path: str, test_mode: bool = False, recognition_mode: str = "fast", language: str = "en", input_type: str = "voice"):
        self.config_path = config_path
        self.test_mode = test_mode
        self.recognition_mode = recognition_mode
        self.event_bus = EventBus()
        self.config = ConfigLoader.load_yaml(config_path)
        self.models_config = self._load_models_config()
        self.vts_service = None
        self.intent_resolver = None
        self.input_processor = None
        self.current_language = language
        self.input_type = input_type

        # Load selected hardware from config
        vts_settings = self.config.get('vts_settings', {})
        self.selected_microphone_name = vts_settings.get('selected_microphone_name', 'Default')
        self.selected_webcam_index = vts_settings.get('selected_webcam_index', 0)

        # Emotion detection specific
        self.emotion_cooldowns = {}
        self.emotion_mappings = self.config.get('emotion_mappings', {})
        self.available_vts_expression_names = [] # Initialize here

    def _load_models_config(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_config_path = os.path.join(base_path, 'config', 'models.yaml')
        return ConfigLoader.load_yaml(models_config_path) # Use ConfigLoader

    async def set_language(self, language: str):
        if not self.models_config:
            logger.error("Models configuration not loaded. Cannot switch language.")
            return

        self.current_language = language
        logger.info(f"Attempting to set ASR language to: {language}")

        selected_model_config = self.models_config.get(language.lower())
        if not selected_model_config:
            logger.error(f"Language '{language}' not supported in models.yaml. Please check the config.")
            return

        model_url = selected_model_config["url"]
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_base_dir = os.path.join(base_path, "models")

        # Instantiate the correct ASR processor based on configuration (currently only SherpaOnnxASRProcessor)
        self.input_processor = SherpaOnnxASRProcessor(event_bus=self.event_bus)
        await self.input_processor.initialize(config=selected_model_config, language=language, model_url=model_url, model_base_dir=model_base_dir, microphone_name=self.selected_microphone_name)
        logger.info(f"Successfully initialized ASR for language: {language}")

    async def _initialize_components(self):
        if not self.config:
            logger.error("Initialization failed: Configuration is not loaded.")
            return

        vts_settings = self.config['vts_settings']
        self.vts_service = VTubeStudioService(
            host=vts_settings['vts_host'],
            port=vts_settings['vts_port'],
            token_file=vts_settings['token_file'],
            event_bus=self.event_bus
        )

        await self.vts_service.connect()
        await self.vts_service.authenticate()

        expression_map, self.available_vts_expression_names = await self._synchronize_expressions()
        if not expression_map:
            expression_map = {}

        self.intent_resolver = KeywordIntentResolver(self.event_bus, expression_map)

        if self.test_mode:
            logger.info("--- RUNNING IN TEST MODE ---")
            self.input_processor = TestInputProcessor(self.event_bus)
            await self.input_processor.initialize(config={}, language="en")
        elif self.input_type == "emotion_detection":
            logger.info("--- RUNNING IN EMOTION DETECTION MODE (WEBCAM INPUT) ---")
            self.input_processor = CnnEmotionDetector(event_bus=self.event_bus)
            emotion_config = self.config.get("emotion_detection_settings", {})
            emotion_config["webcam_index"] = self.selected_webcam_index # Override with selected webcam
            await self.input_processor.initialize(config=emotion_config)
        else: # Default to voice recognition
            logger.info("--- RUNNING IN VOICE RECOGNITION MODE (MICROPHONE INPUT) ---")
            await self.set_language(self.current_language)

    async def run(self):
        logger.debug("ApplicationCore.run() entered.")
        await self._initialize_components()

        if not self.input_processor:
            logger.error("No input processor was initialized. Aborting run.")
            return

        logger.info("Starting application components...")
        tasks = [
            asyncio.create_task(self.intent_resolver.resolve_intent()),
            asyncio.create_task(self._input_consumer()),
            asyncio.create_task(self._handle_hotkey_events()),
        ]

        if self.input_type == "emotion_detection":
            tasks.append(asyncio.create_task(self._handle_emotion_events()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Application tasks were cancelled.")
        finally:
            logger.info("Shutting down application components...")
            if self.vts_service:
                await self.vts_service.disconnect()
            if self.input_processor:
                if isinstance(self.input_processor, ASRProcessor):
                    await self.input_processor.stop_listening()
                elif isinstance(self.input_processor, EmotionProcessor):
                    await self.input_processor.stop_detection()

    async def _handle_emotion_events(self):
        """Consumes emotion detection events and triggers VTS hotkeys based on mappings and cooldowns."""
        emotion_queue = await self.event_bus.subscribe("emotion_detected")
        while True:
            try:
                event = await emotion_queue.get()
                detected_emotion = event.payload.get("emotion")
                
                if detected_emotion and detected_emotion in self.emotion_mappings:
                    hotkey_id = self.emotion_mappings[detected_emotion]
                    
                    if hotkey_id and hotkey_id != "null": # Check if a mapping exists and is not explicitly null
                        current_time = asyncio.get_event_loop().time()
                        last_triggered_time = self.emotion_cooldowns.get(hotkey_id, 0)

                        if (current_time - last_triggered_time) > EMOTION_COOLDOWN_SECONDS:
                            logger.info(f"Emotion '{detected_emotion}' detected. Triggering VTS hotkey: {hotkey_id}")
                            await self.vts_service.trigger_hotkey(hotkey_id)
                            self.emotion_cooldowns[hotkey_id] = current_time
                            await self.event_bus.publish("hotkey_triggered", hotkey_id)
                        else:
                            logger.debug(f"Emotion '{detected_emotion}' detected, but hotkey '{hotkey_id}' is on cooldown.")
                emotion_queue.task_done()
            except asyncio.CancelledError:
                logger.info("Emotion event handler task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in emotion event handler: {e}")

    async def _handle_hotkey_events(self):
        """Consumes hotkey triggered events and triggers VTS hotkeys."""
        hotkey_queue = await self.event_bus.subscribe("hotkey_triggered")
        while True:
            try:
                event = await hotkey_queue.get()
                hotkey_id = event.payload
                logger.info(f"Hotkey event received. Triggering VTube Studio hotkey: {hotkey_id}")
                await self.vts_service.trigger_hotkey(hotkey_id)
                hotkey_queue.task_done()
            except asyncio.CancelledError:
                logger.info("Hotkey event handler task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in hotkey event handler: {e}")

    async def _input_consumer(self):
        """Consumes inputs from the active input processor and publishes them to the event bus."""
        try:
            if hasattr(self.input_processor, 'start_listening'):
                async for _ in self.input_processor.start_listening():
                    pass
            elif hasattr(self.input_processor, 'start_detection'):
                async for _ in self.input_processor.start_detection():
                    pass
        except asyncio.CancelledError:
            logger.info("Input consumer task cancelled.")
        except Exception as e:
            logger.error(f"Error in input consumer: {e}")

    async def _get_vts_expressions(self):
        """Fetches the list of expressions from VTube Studio."""
        try:
            hotkey_list_response = await self.vts_service.get_hotkey_list()
            logger.debug(f"VTS hotkey response: {hotkey_list_response}")
            if hotkey_list_response and 'data' in hotkey_list_response and 'availableHotkeys' in hotkey_list_response['data']:
                return [h for h in hotkey_list_response['data']['availableHotkeys'] if h.get('type') == 'ToggleExpression']
        except Exception as e:
            logger.error(f"Failed to get expressions from VTube Studio: {e}")
        return []

    def _update_config_expressions(self, vts_expressions, yaml_expressions):
        """Updates the local config with new expressions from VTube Studio."""
        new_yaml_expressions = {}
        updated = False
        for exp in vts_expressions:
            exp_file = exp.get('file')
            exp_name = exp.get('name')
            if not exp_file or not exp_name:
                continue
            if exp_file in yaml_expressions:
                new_yaml_expressions[exp_file] = yaml_expressions[exp_file]
            else:
                placeholder_keyword = f"NEW_KEYWORD_{exp_name.replace(' ', '_')}"
                new_yaml_expressions[exp_file] = {
                    'name': exp_name,
                    'keywords': [placeholder_keyword],
                    'cooldown_s': 60
                }
                updated = True
        if len(new_yaml_expressions) != len(yaml_expressions):
            updated = True
        if updated:
            self.config['expressions'] = new_yaml_expressions
            ConfigLoader.save_yaml(self.config_path, self.config)
            logger.info(f"Successfully updated '{self.config_path}' with the latest expressions.")
        return new_yaml_expressions

    def _build_session_expression_map(self, new_yaml_expressions, file_to_hotkey_id_map):
        """Builds the in-memory expression map for the current session."""
        session_expression_map = {}
        for exp_file, exp_data in new_yaml_expressions.items():
            hotkey_id = file_to_hotkey_id_map.get(exp_file)
            if hotkey_id:
                cooldown = exp_data.get('cooldown_s', 60)
                trigger_data = {"hotkeyID": hotkey_id, "cooldown_s": cooldown}
                for keyword in exp_data.get('keywords', []):
                    session_expression_map[keyword] = trigger_data
                session_expression_map[exp_data['name']] = trigger_data
        logger.info(f"Expression map created with {len(session_expression_map)} keywords. Ready to detect keywords.")
        return session_expression_map

    async def _synchronize_expressions(self):
        logger.info("Checking for expression updates from VTube Studio...")
        try:
            vts_expressions = await self._get_vts_expressions()
            logger.debug(f"Found {len(vts_expressions)} ToggleExpression hotkeys in VTS.")

            if vts_expressions:
                yaml_expressions = self.config.get('expressions', {})
                if not yaml_expressions:
                    logger.warning("No expressions found in vts_config.yaml")
                
                new_yaml_expressions = self._update_config_expressions(vts_expressions, yaml_expressions)
                file_to_hotkey_id_map = {exp.get('file'): exp.get('hotkeyID') for exp in vts_expressions}
                session_expression_map = self._build_session_expression_map(new_yaml_expressions, file_to_hotkey_id_map)
                
                self.available_vts_expression_names = [exp.get('name') for exp in vts_expressions if exp.get('name')]
                return session_expression_map, self.available_vts_expression_names
            else:
                logger.warning("Received no or malformed hotkey data from VTube Studio.")

        except Exception as e:
            logger.error(f"Failed to auto-update expressions: {e}")
        
        logger.error("Expression synchronization failed. Returning empty map and list.")
        self.available_vts_expression_names = []
        return {}, []

    async def get_vts_expressions(self):
        """Public method to get VTS expressions for the UI."""
        if not self.vts_service:
            vts_settings = self.config['vts_settings']
            self.vts_service = VTubeStudioService(
                host=vts_settings['vts_host'],
                port=vts_settings['vts_port'],
                token_file=vts_settings['token_file'],
                event_bus=self.event_bus
            )
            await self.vts_service.connect()
            await self.vts_service.authenticate()

        vts_expressions = await self._get_vts_expressions()
        self.available_vts_expression_names = [exp.get('name') for exp in vts_expressions if exp.get('name')]
        return self.available_vts_expression_names