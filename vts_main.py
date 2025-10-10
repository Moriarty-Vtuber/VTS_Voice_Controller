import asyncio
import argparse
from loguru import logger
import os

from core.application_core import ApplicationCore

async def main():
    parser = argparse.ArgumentParser(description="VTS Voice Controller")
    parser.add_argument("--test", action="store_true", help="Run in test mode with a simulated voice command.")
    parser.add_argument("--mode", type=str, choices=['fast', 'accurate'], default='fast', help="Set the recognition mode: 'fast' for low latency, 'accurate' for higher accuracy.")
    args = parser.parse_args()

    # --- Setup Logging ---
    if not os.path.exists("logs"):
        os.mkdir("logs")
    log_path = os.path.join("logs", "vts_controller.log")
    logger.add(log_path, rotation="10 MB", retention="7 days", level="INFO", backtrace=True, diagnose=True)

    config_path = "vts_config.yaml"
    app = ApplicationCore(config_path, test_mode=args.test, recognition_mode=args.mode)
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user.")
