import asyncio
import cv2
import numpy as np
import onnxruntime
from loguru import logger
from typing import AsyncGenerator
import os
import requests
from tqdm import tqdm

from core.event_bus import EventBus
from core.interfaces import EmotionProcessor

# Model and label definitions
MODEL_URL = "https://huggingface.co/webml/models-moved/resolve/0e73dc31942fbdbbd135d85be5e5321eee88a826/emotion-ferplus-8.onnx"
MODEL_DIR = "models/emotion_model"
MODEL_PATH = os.path.join(MODEL_DIR, "emotion-ferplus-8.onnx")
EMOTION_LABELS = ['neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disgust', 'fear', 'contempt']

def ensure_model_downloaded(url, path):
    """Downloads the ONNX model if not already present."""
    if os.path.exists(path):
        logger.info(f"✅ Emotion model already exists at {path}. Skipping download.")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    logger.info(f"Downloading emotion model from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(path, 'wb') as f, tqdm(
                desc=os.path.basename(path),
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    bar.update(size)
        logger.info("Download complete.")
    except Exception as e:
        logger.error(f"Failed to download emotion model: {e}")
        raise

class CnnEmotionDetector(EmotionProcessor):
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.cap = None
        self.running = False
        self.detected_emotion = "neutral"
        self.webcam_index = 0
        self.session = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    async def initialize(self, config: dict):
        self.webcam_index = config.get("webcam_index", 0)
        logger.info(f"EmotionDetector: Initializing with webcam index {self.webcam_index}")

        # Download and load the ONNX model
        ensure_model_downloaded(MODEL_URL, MODEL_PATH)
        try:
            self.session = onnxruntime.InferenceSession(MODEL_PATH)
            logger.info("ONNX emotion recognition model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            raise

        await self.event_bus.publish("emotion_detector_status", "Initialized")

    async def start_detection(self) -> AsyncGenerator[dict, None]:
        self.running = True
        self.cap = cv2.VideoCapture(self.webcam_index)
        if not self.cap.isOpened():
            logger.error(f"Could not open webcam at index {self.webcam_index}")
            await self.event_bus.publish("emotion_detector_status", "Error: Webcam not found")
            self.running = False
            return

        logger.info("Starting real-time facial expression detection...")
        await self.event_bus.publish("emotion_detector_status", "Detecting")

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to grab frame from webcam.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(faces) > 0:
                (x, y, w, h) = faces[0] # Process only the first detected face
                face_roi = gray[y:y+h, x:x+w]

                # Preprocess the face for the model
                resized_face = cv2.resize(face_roi, (64, 64), interpolation=cv2.INTER_AREA)
                normalized_face = resized_face.astype(np.float32) / 255.0
                input_tensor = np.expand_dims(np.expand_dims(normalized_face, axis=0), axis=0)

                # Run inference
                input_name = self.session.get_inputs()[0].name
                output_name = self.session.get_outputs()[0].name
                result = self.session.run([output_name], {input_name: input_tensor})
                
                # Post-process
                probabilities = result[0][0]
                emotion_index = np.argmax(probabilities)
                current_emotion = EMOTION_LABELS[emotion_index]

                if current_emotion != self.detected_emotion:
                    self.detected_emotion = current_emotion
                    logger.debug(f"Detected emotion: {self.detected_emotion}")
                    await self.event_bus.publish("emotion_detected", {"emotion": self.detected_emotion})
                    yield {"emotion": self.detected_emotion}

            await asyncio.sleep(0.1) # Yield control to the event loop

        self.running = False
        if self.cap:
            self.cap.release()
        logger.info("Detection stopped.")
        await self.event_bus.publish("emotion_detector_status", "Stopped")

    async def stop_detection(self):
        self.running = False
        logger.info("Stopping emotion detection...")
        if self.cap:
            self.cap.release()
        await self.event_bus.publish("emotion_detector_status", "Stopped")

    async def get_detected_emotion(self) -> str:
        return self.detected_emotion
