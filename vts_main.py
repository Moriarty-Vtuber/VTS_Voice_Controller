import asyncio
from loguru import logger
import os
import sys

from ui.app_ui import main as ui_main

async def main():
    # --- Setup Logging ---
    if not os.path.exists("logs"):
        os.mkdir("logs")
    log_path = os.path.join("logs", "vts_controller.log")
    logger.add(log_path, rotation="10 MB", retention="7 days", level="INFO", backtrace=True, diagnose=True)

    await ui_main()

if __name__ == "__main__":
    try:
        # Add a workaround for a known issue with qasync and Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user.")
