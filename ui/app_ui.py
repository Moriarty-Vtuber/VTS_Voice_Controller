import asyncio
import sys
import yaml
import os
from loguru import logger

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from core.application_core import ApplicationCore
from inputs.utils.device_utils import get_audio_input_devices, get_webcam_devices

def load_initial_config():
    try:
        # Go up one level from the current file's directory to the project root
        config_path = os.path.join(os.path.dirname(__file__), '..', 'vts_config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load initial config: {e}")
        return None

class AppUI:
    def __init__(self):
        self.app_core_task = None
        self.current_language = "en"
        self.app_core = None

        # Initial UI setup
        config_path = os.path.join(os.path.dirname(__file__), '..', 'vts_config.yaml')
        self.config_path = config_path # Store config_path for later use
        initial_config = load_initial_config()
        
        self.main_window = MainWindow(config_path=config_path, initial_config=initial_config if initial_config is not None else {})

        # Connect signals
        self.main_window.start_button.clicked.connect(self._start_button_clicked)
        self.main_window.stop_button.clicked.connect(self._stop_button_clicked)
        self.main_window.language_selector.currentTextChanged.connect(self._language_changed)
        self.main_window.microphone_selector.currentTextChanged.connect(self._microphone_changed)
        self.main_window.webcam_selector.currentTextChanged.connect(self._webcam_changed)
        self.main_window.input_type_selector.currentTextChanged.connect(self._input_type_changed)

        # Populate device selectors
        self._populate_microphone_selector(initial_config)
        self._populate_webcam_selector(initial_config)

        if initial_config:
            self.main_window.populate_keyword_editor(initial_config.get('expressions', {}))
        else:
            logger.warning("Initial config not loaded, starting with empty expressions.")
        
        logger.debug(f"AppUI: Before show() - Central Widget Visible={self.main_window.centralWidget().isVisible()}, Emotion Editor Frame Visible={self.main_window.emotion_editor_frame.isVisible()}")
        self.main_window.show()
        logger.debug(f"AppUI: After show() - Central Widget Visible={self.main_window.centralWidget().isVisible()}, Emotion Editor Frame Visible={self.main_window.emotion_editor_frame.isVisible()}")

        # Populate emotion editor on startup with existing mappings and an empty list for available VTS expressions
        self.main_window.populate_emotion_editor(
            initial_config.get('emotion_mappings', {}),
            [] # Available VTS expressions are not fetched yet at this stage
        )
        self.main_window.emotion_editor_frame.repaint() # Force repaint after populating

        # Set initial state of mode_selector based on current input_type_selector selection
        self._input_type_changed(self.main_window.input_type_selector.currentText())

    async def initialize(self):
        """Asynchronously initializes components that require an event loop."""
        await self.populate_vts_expressions()

    async def populate_vts_expressions(self):
        """Fetches VTS expressions and populates the UI."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'vts_config.yaml')
        self.app_core = ApplicationCore(config_path=config_path)
        expressions = await self.app_core.get_vts_expressions()
        self.main_window.populate_emotion_editor(
            self.app_core.config.get('emotion_mappings', {}),
            expressions
        )

    def _save_config_setting(self, section: str, key: str, value: any):
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            if config is None: # Handle empty config file
                config = {}
            if section not in config:
                config[section] = {}
            config[section][key] = value
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(config, f)
            logger.info(f"Config updated: {section}.{key} = {value}")
        except Exception as e:
            logger.error(f"Failed to save config setting {section}.{key}: {e}")

    def _populate_microphone_selector(self, initial_config: dict):
        devices = get_audio_input_devices()
        self.main_window.microphone_selector.clear()
        current_mic_name = initial_config.get('vts_settings', {}).get('selected_microphone_name', 'Default')
        
        default_mic_index = -1
        for i, dev in enumerate(devices):
            self.main_window.microphone_selector.addItem(dev['name'])
            if dev['name'] == current_mic_name:
                default_mic_index = i
        
        if default_mic_index != -1:
            self.main_window.microphone_selector.setCurrentIndex(default_mic_index)
        elif devices:
            # If the saved mic is not found, select the first available and save it
            self.main_window.microphone_selector.setCurrentIndex(0)
            self._save_config_setting('vts_settings', 'selected_microphone_name', devices[0]['name'])
        else:
            self.main_window.microphone_selector.addItem("No Microphones Found")
            self.main_window.microphone_selector.setEnabled(False)

    def _populate_webcam_selector(self, initial_config: dict):
        devices = get_webcam_devices()
        self.main_window.webcam_selector.clear()
        current_webcam_index = initial_config.get('vts_settings', {}).get('selected_webcam_index', 0)

        default_webcam_idx = -1
        for i, dev in enumerate(devices):
            self.main_window.webcam_selector.addItem(dev['name'])
            if dev['index'] == current_webcam_index:
                default_webcam_idx = i
        
        if default_webcam_idx != -1:
            self.main_window.webcam_selector.setCurrentIndex(default_webcam_idx)
        elif devices:
            # If the saved webcam is not found, select the first available and save it
            self.main_window.webcam_selector.setCurrentIndex(0)
            self._save_config_setting('vts_settings', 'selected_webcam_index', devices[0]['index'])
        else:
            self.main_window.webcam_selector.addItem("No Webcams Found")
            self.main_window.webcam_selector.setEnabled(False)

    def _microphone_changed(self, text: str):
        if text and text != "No Microphones Found":
            self._save_config_setting('vts_settings', 'selected_microphone_name', text)

    def _webcam_changed(self, text: str):
        if text and text != "No Webcams Found":
            # Find the index corresponding to the selected name
            devices = get_webcam_devices()
            selected_index = next((dev['index'] for dev in devices if dev['name'] == text), 0)
            self._save_config_setting('vts_settings', 'selected_webcam_index', selected_index)

    def _language_changed(self, language: str):
        logger.info(f"--- UI: Language set to {language} for next run ---")
        self.current_language = language
        self.main_window.retranslate_ui(language)

    def _input_type_changed(self, text: str):
        if text == self.main_window.tr("input_type_emotion"):
            self.main_window.mode_selector.setEnabled(False)
        else:
            self.main_window.mode_selector.setEnabled(True)

    def __init__(self):
        self.app_core_task = None
        self.current_language = "en"
        self.app_core = None

        # Initial UI setup
        config_path = os.path.join(os.path.dirname(__file__), '..', 'vts_config.yaml')
        self.config_path = config_path # Store config_path for later use
        initial_config = load_initial_config()

        self.main_window = MainWindow(config_path=config_path, initial_config=initial_config if initial_config is not None else {})

        # Connect signals
        self.main_window.start_button.clicked.connect(self._start_button_clicked)
        self.main_window.stop_button.clicked.connect(self._stop_button_clicked)
        self.main_window.language_selector.currentTextChanged.connect(self._language_changed)
        self.main_window.microphone_selector.currentTextChanged.connect(self._microphone_changed)
        self.main_window.webcam_selector.currentTextChanged.connect(self._webcam_changed)
        self.main_window.input_type_selector.currentTextChanged.connect(self._input_type_changed)

        # Populate device selectors
        self._populate_microphone_selector(initial_config)
        self._populate_webcam_selector(initial_config)

        if initial_config:
            self.main_window.populate_keyword_editor(initial_config.get('expressions', {}))
        else:
            logger.warning("Initial config not loaded, starting with empty expressions.")

        logger.debug(f"AppUI: Before show() - Central Widget Visible={self.main_window.centralWidget().isVisible()}, Emotion Editor Frame Visible={self.main_window.emotion_editor_frame.isVisible()}")
        self.main_window.show()
        logger.debug(f"AppUI: After show() - Central Widget Visible={self.main_window.centralWidget().isVisible()}, Emotion Editor Frame Visible={self.main_window.emotion_editor_frame.isVisible()}")

        # Populate emotion editor on startup with existing mappings and an empty list for available VTS expressions
        asyncio.create_task(self.populate_vts_expressions())
        self.main_window.emotion_editor_frame.repaint() # Force repaint after populating

        # Set initial state of mode_selector based on current input_type_selector selection
        self._input_type_changed(self.main_window.input_type_selector.currentText())

    async def populate_vts_expressions(self):
        """Fetches VTS expressions and populates the UI."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'vts_config.yaml')
        self.app_core = ApplicationCore(config_path=config_path)
        expressions = await self.app_core.get_vts_expressions()
        self.main_window.populate_emotion_editor(
            self.app_core.config.get('emotion_mappings', {}),
            expressions
        )

    def _start_button_clicked(self):
        logger.info("--- UI: Start button clicked ---")
        self.app_core_task = asyncio.create_task(self.start_application())

    def _stop_button_clicked(self):
        logger.info("--- UI: Stop button clicked ---")
        if self.app_core_task:
            self.app_core_task.cancel()

    async def start_application(self):
        self.main_window.set_status(app="Starting...")
        self.main_window.start_button.setEnabled(False)
        self.main_window.mode_selector.setEnabled(False)
        self.main_window.language_selector.setEnabled(False)
        self.main_window.input_type_selector.setEnabled(False)
        self.main_window.microphone_selector.setEnabled(False)
        self.main_window.webcam_selector.setEnabled(False)
        self.main_window.stop_button.setEnabled(True)

        recognition_mode = self.main_window.mode_selector.currentText()
        ui_input_type = self.main_window.input_type_selector.currentText()
        
        # Map UI input type string to internal code string
        if ui_input_type == self.main_window.tr("input_type_emotion"):
            input_type = "emotion_detection"
        else:
            input_type = "voice" # Default to voice

        self.app_core.recognition_mode = recognition_mode
        self.app_core.language = self.current_language
        self.app_core.input_type = input_type

        # Setup listeners on the running instance
        transcription_queue = await self.app_core.event_bus.subscribe("transcription_received")
        hotkey_queue = await app_core.event_bus.subscribe("hotkey_triggered")
        vts_status_queue = await app_core.event_bus.subscribe("vts_status_update")
        asr_status_queue = await app_core.event_bus.subscribe("asr_status_update")
        asr_ready_queue = await app_core.event_bus.subscribe("asr_ready")
        emotion_detected_queue = await app_core.event_bus.subscribe("emotion_detected")
        vts_model_changed_queue = await app_core.event_bus.subscribe("vts_model_changed")


        listener_tasks = [
            asyncio.create_task(self._handle_transcription_events(transcription_queue)),
            asyncio.create_task(self._handle_hotkey_events(hotkey_queue)),
            asyncio.create_task(self._handle_vts_status_events(vts_status_queue)),
            asyncio.create_task(self._handle_asr_status_events(asr_status_queue)),
            asyncio.create_task(self._handle_asr_ready_events(asr_ready_queue)),
            asyncio.create_task(self._handle_emotion_detected_events(emotion_detected_queue)),
            asyncio.create_task(self._handle_vts_model_changed_events(vts_model_changed_queue)),
        ]

        try:
            logger.debug("Attempting to run app_core...")
            await self.app_core.run()
        except asyncio.CancelledError:
            logger.info("Application core task was cancelled by UI.")
        finally:
            for task in listener_tasks:
                task.cancel()
                try:
                    await task # Await cancellation to allow graceful cleanup
                except asyncio.CancelledError:
                    pass
            self.main_window.set_status(app="Stopped", vts="Disconnected", asr="Idle")
            self.main_window.start_button.setEnabled(True)
            self.main_window.mode_selector.setEnabled(True)
            self.main_window.language_selector.setEnabled(True)
            self.main_window.input_type_selector.setEnabled(True)
            self.main_window.microphone_selector.setEnabled(True)
            self.main_window.webcam_selector.setEnabled(True)
            self.main_window.stop_button.setEnabled(False)

    async def _handle_transcription_events(self, queue: asyncio.Queue):
        while True:
            try:
                event = await queue.get()
                self.main_window.append_log(f"Heard: {event.payload}")
                queue.task_done()
            except asyncio.CancelledError:
                break

    async def _handle_vts_model_changed_events(self, queue: asyncio.Queue):
        while True:
            try:
                event = await queue.get()
                new_expressions = event.payload.get("expressions", [])
                self.main_window.append_log("VTube Studio model changed. Updating expression list...")

                # We need the current emotion mappings to repopulate correctly
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                emotion_mappings = config.get('emotion_mappings', {})

                self.main_window.populate_emotion_editor(emotion_mappings, new_expressions)
                queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error handling VTS model changed event: {e}")

    async def _handle_hotkey_events(self, queue: asyncio.Queue):
        while True:
            try:
                event = await queue.get()
                self.main_window.append_log(f">>> Triggered: {event.payload}")
                queue.task_done()
            except asyncio.CancelledError:
                break

    async def _handle_vts_status_events(self, queue: asyncio.Queue):
        while True:
            try:
                event = await queue.get()
                self.main_window.set_status(vts=event.payload)
                queue.task_done()
            except asyncio.CancelledError:
                break

    async def _handle_asr_status_events(self, queue: asyncio.Queue):
        while True:
            try:
                event = await queue.get()
                self.main_window.set_status(asr=event.payload)
                queue.task_done()
            except asyncio.CancelledError:
                break

    async def _handle_asr_ready_events(self, queue: asyncio.Queue):
        while True:
            try:
                await queue.get()
                self.main_window.set_status(app="Running")
                queue.task_done()
            except asyncio.CancelledError:
                break

    async def _handle_emotion_detected_events(self, queue: asyncio.Queue):
        while True:
            try:
                event = await queue.get()
                self.main_window.append_log(f"Emotion Detected: {event.payload.get('emotion')}")
                queue.task_done()
            except asyncio.CancelledError:
                break