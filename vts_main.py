import asyncio
from loguru import logger
import os

from core.application_core import ApplicationCore

async def main():
    # --- Setup Logging ---
    if not os.path.exists("logs"):
        os.mkdir("logs")
    log_path = os.path.join("logs", "vts_controller.log")
    logger.add(log_path, rotation="10 MB", retention="7 days", level="INFO", backtrace=True, diagnose=True)

    config_path = "vts_config.yaml"
    app = ApplicationCore(config_path)
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user.")