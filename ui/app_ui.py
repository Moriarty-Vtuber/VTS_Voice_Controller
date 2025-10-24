import asyncio
import sys
import yaml
import os
from loguru import logger

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from core.application_core import ApplicationCore

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

        # Initial UI setup
        config_path = os.path.join(os.path.dirname(__file__), '..', 'vts_config.yaml')
        initial_config = load_initial_config()
        
        self.main_window = MainWindow(config_path=config_path, initial_config=initial_config if initial_config is not None else {})

        # Connect signals
        self.main_window.start_button.clicked.connect(self._start_button_clicked)
        self.main_window.stop_button.clicked.connect(self._stop_button_clicked)
        self.main_window.language_selector.currentTextChanged.connect(self._language_changed)

        if initial_config:
            self.main_window.populate_keyword_editor(initial_config.get('expressions', {}))
        else:
            logger.warning("Initial config not loaded, starting with empty expressions.")
        
        self.main_window.show()

    def _language_changed(self, language: str):
        logger.info(f"--- UI: Language set to {language} for next run ---")
        self.current_language = language
        self.main_window.retranslate_ui(language)

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
        self.main_window.stop_button.setEnabled(True)

        recognition_mode = self.main_window.mode_selector.currentText()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'vts_config.yaml')
        app_core = ApplicationCore(
            config_path=config_path,
            recognition_mode=recognition_mode,
            language=self.current_language
        )

        # Setup listeners on the running instance
        transcription_queue = await app_core.event_bus.subscribe("transcription_received")
        hotkey_queue = await app_core.event_bus.subscribe("hotkey_triggered")
        vts_status_queue = await app_core.event_bus.subscribe("vts_status_update")
        asr_status_queue = await app_core.event_bus.subscribe("asr_status_update")
        asr_ready_queue = await app_core.event_bus.subscribe("asr_ready")

        listener_tasks = [
            asyncio.create_task(self._handle_transcription_events(transcription_queue)),
            asyncio.create_task(self._handle_hotkey_events(hotkey_queue)),
            asyncio.create_task(self._handle_vts_status_events(vts_status_queue)),
            asyncio.create_task(self._handle_asr_status_events(asr_status_queue)),
            asyncio.create_task(self._handle_asr_ready_events(asr_ready_queue)),
        ]

        try:
            logger.debug("Attempting to run app_core...")
            await app_core.run()
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
            self.main_window.stop_button.setEnabled(False)

    async def _handle_transcription_events(self, queue: asyncio.Queue):
        while True:
            try:
                event = await queue.get()
                self.main_window.append_log(f"Heard: {event.payload}")
                queue.task_done()
            except asyncio.CancelledError:
                break

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