import sounddevice as sd
import cv2
from loguru import logger

def get_audio_input_devices():
    """
    Returns a list of available audio input devices.
    Each device is represented as a dictionary with 'name' and 'index'.
    """
    devices = []
    try:
        device_list = sd.query_devices()
        for i, device in enumerate(device_list):
            if device['max_input_channels'] > 0:
                devices.append({'name': device['name'], 'index': i})
    except Exception as e:
        logger.error(f"Error querying audio devices: {e}")
    return devices

def get_webcam_devices():
    """
    Returns a list of available webcam devices.
    Each device is represented as a dictionary with 'name' and 'index'.
    """
    devices = []
    for i in range(10):  # Check up to 10 potential webcam indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Attempt to get a more descriptive name if available, otherwise use generic
            # OpenCV doesn't easily expose device names directly, so we use index
            devices.append({'name': f"Webcam {i}", 'index': i})
            cap.release()
        else:
            # If we fail to open a camera, it might mean we've gone past available ones
            # or there's a permission issue. We can stop checking after a few failures.
            # For simplicity, we'll just continue for now.
            pass
    return devices

if __name__ == '__main__':
    logger.info("Available Audio Input Devices:")
    for dev in get_audio_input_devices():
        logger.info(f"  Name: {dev['name']}, Index: {dev['index']}")

    logger.info("\nAvailable Webcam Devices:")
    for dev in get_webcam_devices():
        logger.info(f"  Name: {dev['name']}, Index: {dev['index']}")
