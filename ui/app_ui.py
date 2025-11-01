import asyncio
import yaml
import os
from loguru import logger

from ui.main_window import MainWindow
from core.application_core import ApplicationCore
from inputs.utils.device_utils import get_audio_input_devices


class AppUI:
    def __init__(self):
        self.app_core_task = None
        self.app_core = None  # Will be initialized asynchronously
        self.current_language = "en"
        self.listener_tasks = []

        self.config_path = os.path.join(
            os.path.dirname(__file__), '..', 'vts_config.yaml')
        self.initial_config = self._load_initial_config()

        self.main_window = MainWindow(
            config_path=self.config_path, initial_config=self.initial_config)

        self._connect_signals()
        self._populate_microphone_selector()

        if self.initial_config:
            self.main_window.populate_keyword_editor(
                self.initial_config.get('expressions', {}))

        self.main_window.show()

    def _load_initial_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config if config is not None else {}
        except FileNotFoundError:
            logger.warning(
                f"Config file not found at {self.config_path}. A new one will be created on first save/sync.")
            return {}

    def _connect_signals(self):
        self.main_window.start_button.clicked.connect(
            self._start_button_clicked)
        self.main_window.stop_button.clicked.connect(self._stop_button_clicked)
        self.main_window.language_selector.currentTextChanged.connect(
            self._language_changed)
        self.main_window.microphone_selector.currentTextChanged.connect(
            self._microphone_changed)

    async def initialize(self):
        """Asynchronously initializes components that require an event loop, like ApplicationCore."""
        logger.debug("AppUI initializing...")
        self.app_core = ApplicationCore(config_path=self.config_path)
        await self._update_expressions_from_vts()
        logger.debug("AppUI initialization complete.")

    async def _update_expressions_from_vts(self):
        """Fetches VTS expressions and updates the keyword editor."""
        if not self.app_core:
            return
        await self.app_core.initialize_expression_service()
        logger.info(f"Expressions synchronized with VTube Studio.")
        updated_config = self._load_initial_config()
        self.main_window.populate_keyword_editor(
            updated_config.get('expressions', {}))

    def _save_config_setting(self, section: str, key: str, value: any):
        try:
            config = self._load_initial_config()
            config.setdefault(section, {})[key] = value
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(config, f)
        except Exception as e:
            logger.error(f"Failed to save config setting {section}.{key}: {e}")

    def _populate_microphone_selector(self):
        devices = get_audio_input_devices()
        self.main_window.microphone_selector.clear()

        if not devices:
            self.main_window.microphone_selector.addItem(
                "No Microphones Found")
            self.main_window.microphone_selector.setEnabled(False)
            return

        current_mic_name = self.initial_config.get(
            'vts_settings', {}).get('selected_microphone_name')
        device_names = [dev['name'] for dev in devices]
        self.main_window.microphone_selector.addItems(device_names)

        if current_mic_name in device_names:
            self.main_window.microphone_selector.setCurrentText(
                current_mic_name)
        elif device_names:
            self.main_window.microphone_selector.setCurrentIndex(0)
            self._microphone_changed(device_names[0])

    def _microphone_changed(self, text: str):
        if text and text != "No Microphones Found":
            self._save_config_setting(
                'vts_settings', 'selected_microphone_name', text)

    def _language_changed(self, language_code: str):
        self.current_language = language_code
        self.main_window.retranslate_ui(language_code)

    def _start_button_clicked(self):
        if self.app_core_task and not self.app_core_task.done():
            return
        self.app_core_task = asyncio.create_task(self.start_application())

    def _stop_button_clicked(self):
        if not self.app_core_task or self.app_core_task.done():
            return
        self.app_core_task.cancel()

    async def start_application(self):
        self._set_ui_state(running=True)
        self.app_core.recognition_mode = self.main_window.mode_selector.currentText()
        self.app_core.language = self.current_language

        await self._subscribe_to_events()
        try:
            await self.app_core.run()
        except asyncio.CancelledError:
            logger.info("Application core task was cancelled.")
        finally:
            await self._cleanup_listeners()
            self._set_ui_state(running=False)

    async def _subscribe_to_events(self):
        event_handlers = {
            "transcription_received": self._handle_transcription_events,
            "vts_status_update": self._handle_vts_status_events,
            "asr_status_update": self._handle_asr_status_events,
            "asr_ready": self._handle_asr_ready_events,
        }
        for name, handler in event_handlers.items():
            queue = await self.app_core.event_bus.subscribe(name)
            self.listener_tasks.append(asyncio.create_task(handler(queue)))

    async def _cleanup_listeners(self):
        for task in self.listener_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self.listener_tasks.clear()

    def _set_ui_state(self, running: bool):
        self.main_window.start_button.setEnabled(not running)
        self.main_window.stop_button.setEnabled(running)
        for w in [self.main_window.mode_selector, self.main_window.language_selector, self.main_window.microphone_selector]:
            w.setEnabled(not running)
        self.main_window.set_status(
            app="Starting..." if running else "Stopped", vts="Disconnected", asr="Idle")

    async def _handle_transcription_events(self, queue: asyncio.Queue):
        while True:
            event = await queue.get()
            self.main_window.append_log(f"Heard: {event.payload}")
            queue.task_done()

    async def _handle_vts_status_events(self, queue: asyncio.Queue):
        while True:
            event = await queue.get()
            self.main_window.set_status(vts=event.payload)
            queue.task_done()

    async def _handle_asr_status_events(self, queue: asyncio.Queue):
        while True:
            event = await queue.get()
            self.main_window.set_status(asr=event.payload)
            queue.task_done()

    async def _handle_asr_ready_events(self, queue: asyncio.Queue):
        while True:
            await queue.get()
            self.main_window.set_status(app="Running")
            queue.task_done()
