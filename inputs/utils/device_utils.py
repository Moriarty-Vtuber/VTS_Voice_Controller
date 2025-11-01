from typing import List, Dict
import sounddevice as sd
from loguru import logger


def get_audio_input_devices() -> List[Dict[str, any]]:
    """
    Retrieves a list of available audio input devices.
    """
    try:
        devices = sd.query_devices()
        input_devices = [
            {
                'index': i,
                'name': device['name'],
            }
            for i, device in enumerate(devices)
            if device.get('max_input_channels', 0) > 0
        ]
        return input_devices
    except Exception as e:
        logger.error(f"Could not query audio devices: {e}")
        return []
