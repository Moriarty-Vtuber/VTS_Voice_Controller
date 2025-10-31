import asyncio
import sys
import os
from loguru import logger
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication

from ui.app_ui import AppUI

def main():
    # --- Setup Logging ---
    if not os.path.exists("logs"):
        os.mkdir("logs")
    log_path = os.path.join("logs", "vts_controller.log")
    logger.add(log_path, rotation="10 MB", retention="7 days", level="DEBUG", backtrace=True, diagnose=True)
    logger.add(sys.stdout, level="DEBUG") # Add a sink for stdout to capture print statements

    # --- Set up the asyncio event loop for qasync ---
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # --- Create and run the application ---
    app_ui = AppUI()
    
    with loop:
        asyncio.create_task(app_ui.initialize())
        loop.run_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program terminated by user.")
