import asyncio
import sys
import yaml
from loguru import logger

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop, QApplication as QAsyncApplication

from ui.main_window import MainWindow
from core.application_core import ApplicationCore

def load_initial_config():
    """Synchronously loads the config for initial UI population."""
    try:
        with open("vts_config.yaml", 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("vts_config.yaml not found. UI will be empty on start.")
        return None
    except Exception as e:
        logger.error(f"Error loading initial config: {e}")
        return None

class AppUI:
    def __init__(self):
        self.app = QAsyncApplication(sys.argv)
        self.main_window = MainWindow()
        self.app_core_task = None

        self.main_window.start_button.clicked.connect(self._start_button_clicked)
        self.main_window.stop_button.clicked.connect(self.stop_application)

    def _start_button_clicked(self):
        """Synchronous slot to trigger the async start_application task."""
        asyncio.create_task(self.start_application())

    async def start_application(self):
        logger.info("UI: Start button clicked.")
        self.main_window.set_status(app="Starting...")
        self.main_window.start_button.setEnabled(False)
        self.main_window.mode_selector.setEnabled(False)
        self.main_window.stop_button.setEnabled(True)

        recognition_mode = self.main_window.mode_selector.currentText()
        app_core = ApplicationCore(
            config_path="vts_config.yaml",
            recognition_mode=recognition_mode
        )
        
        self.app_core_task = asyncio.create_task(self.run_app_core(app_core))

    def stop_application(self):
        logger.info("UI: Stop button clicked.")
        self.main_window.set_status(app="Stopping...")
        if self.app_core_task:
            self.app_core_task.cancel()
        # UI state will be reset in the finally block of run_app_core

    async def run_app_core(self, app_core: ApplicationCore):
        # Setup listeners on the actual running instance
        transcription_queue = await app_core.event_bus.subscribe("transcription_received")
        hotkey_queue = await app_core.event_bus.subscribe("hotkey_triggered")
        
        listener_tasks = [
            asyncio.create_task(self._handle_transcription_events(transcription_queue)),
            asyncio.create_task(self._handle_hotkey_events(hotkey_queue)),
        ]

        try:
            await app_core.run()
        except asyncio.CancelledError:
            logger.info("Application core task was cancelled by UI.")
        except Exception as e:
            logger.error(f"An error occurred in the application core: {e}")
            self.main_window.append_log(f"[ERROR] {e}")
        finally:
            for task in listener_tasks:
                task.cancel()
            self.main_window.set_status(app="Stopped", vts="Disconnected", asr="Idle")
            self.main_window.start_button.setEnabled(True)
            self.main_window.mode_selector.setEnabled(True)
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
                self.main_window.append_log(f">>> Triggered Hotkey: {event.payload}")
                queue.task_done()
            except asyncio.CancelledError:
                break

async def main():
    ui = AppUI()
    
    # Populate UI with initial data
    initial_config = load_initial_config()
    if initial_config:
        ui.main_window.populate_keyword_editor(initial_config.get('expressions', {}))

    ui.main_window.show()
    sys.exit(ui.app.exec())

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass