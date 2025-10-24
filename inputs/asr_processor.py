import asyncio
import os
import sounddevice as sd
import numpy as np
import sherpa_onnx
from loguru import logger
import onnxruntime
import webrtcvad
from collections import deque
from typing import AsyncGenerator

from core.interfaces import ASRProcessor
from core.event_bus import EventBus
from inputs.utils.utils import ensure_model_downloaded_and_extracted

class SherpaOnnxASRProcessor(ASRProcessor):
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.recognizer = None
        self.stream = None
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_lock = asyncio.Lock()
        self.last_text = ""
        self.running = False
        self.audio_processing_task = None
        self.transcription_queue = asyncio.Queue()
        self.vad = None
        self.vad_buffer = b''
        self.vad_frame_size = 0
        self.vad_frame_duration_ms = 0
        self.SAMPLE_RATE = 16000
        self.provider = "cpu"
        self.recognition_mode = "fast"
        self.model_dir = ""
        self.model_config = {}
        self.decoding_method = "greedy_search"
        self.debug = False

    async def initialize(self, config: dict, language: str, model_url: str, model_base_dir: str):
        self.model_config = config
        self.model_dir = os.path.join(model_base_dir, self.model_config.get("path", ""))
        self.recognition_mode = config.get("recognition_mode", "fast")
        self.provider = config.get("provider", "cpu")
        self.decoding_method = config.get("decoding_method", "greedy_search")
        self.debug = config.get("debug", False)
        self.SAMPLE_RATE = self.model_config.get("sample_rate", 16000)
        vad_aggressiveness = config.get("vad_aggressiveness", 1)
        self.vad_frame_duration_ms = config.get("vad_frame_duration_ms", 30)

        await self.event_bus.publish("asr_status_update", "Initializing")

        # Ensure model is downloaded and extracted
        actual_model_dir = ensure_model_downloaded_and_extracted(model_url, model_base_dir)
        self.model_dir = actual_model_dir # Set the model_dir to the actual extracted directory

        if self.provider == "cuda":
            try:
                if "CUDAExecutionProvider" not in onnxruntime.get_available_providers():
                    logger.warning("CUDA provider not available for ONNX. Falling back to CPU.")
                    self.provider = "cpu"
            except ImportError:
                logger.warning("ONNX Runtime not installed. Falling back to CPU.")
                self.provider = "cpu"
        logger.info(f"Sherpa-Onnx-ASR: Using {self.provider} for inference")

        self.recognizer = self._create_recognizer()
        self.stream = self.recognizer.create_stream()
        
        # VAD initialization
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.vad_frame_size = int(self.SAMPLE_RATE * self.vad_frame_duration_ms / 1000)
        
        await self.event_bus.publish("asr_status_update", "Ready")

    def _create_recognizer(self):
        model_type = self.model_config.get("model_type", "transducer")
        params = self.model_config["params"]
        logger.info(f"Creating recognizer of type '{model_type}'")

        if model_type == "transducer":
            return sherpa_onnx.OnlineRecognizer.from_transducer(
                tokens=os.path.join(self.model_dir, params["tokens"]),
                encoder=os.path.join(self.model_dir, params["encoder"]),
                decoder=os.path.join(self.model_dir, params["decoder"]),
                joiner=os.path.join(self.model_dir, params["joiner"]),
                num_threads=1,
                sample_rate=self.SAMPLE_RATE,
                feature_dim=80,
                enable_endpoint_detection=True,
                decoding_method=self.decoding_method,
                provider=self.provider,
                debug=self.debug,
                rule3_min_utterance_length=3.0,
            )
        elif model_type == "sense-voice":
            raise NotImplementedError(f"The '{model_type}' model type is not yet supported by the ASRProcessor.")
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")

    def _transcribe_np(self, audio: np.ndarray) -> str:
        self.stream.accept_waveform(self.SAMPLE_RATE, audio)
        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        if self.recognition_mode == "fast":
            result = self.recognizer.get_result(self.stream)
            text = result.strip()

            text_to_return = ""
            if text and text != self.last_text:
                text_to_return = text
                self.last_text = text

            if self.recognizer.is_endpoint(self.stream):
                self.recognizer.reset(self.stream)
                self.last_text = ""
            
            return text_to_return
        
        else: # Accurate mode
            text_to_return = ""
            if self.recognizer.is_endpoint(self.stream):
                result = self.recognizer.get_result(self.stream)
                text_to_return = result.strip()
                self.recognizer.reset(self.stream)
            
            return text_to_return

    async def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(status)

        # Convert float32 to int16 for VAD
        pcm_data = (indata * 32767).astype(np.int16).tobytes()
        self.vad_buffer += pcm_data

        # Process VAD frames
        while len(self.vad_buffer) >= self.vad_frame_size * 2: # 2 bytes per int16 sample
            frame = self.vad_buffer[:self.vad_frame_size * 2]
            self.vad_buffer = self.vad_buffer[self.vad_frame_size * 2:]

            is_speech = self.vad.is_speech(frame, self.SAMPLE_RATE)
            logger.trace(f"VAD frame processed, is_speech: {is_speech}")

            if is_speech:
                # If speech is detected, append to the ASR buffer
                async with self.buffer_lock:
                    # Sherpa-onnx expects float32, so convert back
                    float_frame = np.frombuffer(frame, dtype=np.int16).astype(np.float32) / 32767.0
                    self.audio_buffer = np.concatenate((self.audio_buffer, float_frame))

    async def start_listening(self) -> AsyncGenerator[str, None]:
        self.running = True
        logger.info("Starting microphone stream...")
        await self.event_bus.publish("asr_status_update", "Listening")
        loop = asyncio.get_running_loop()

        def sync_audio_callback(indata, frames, time, status):
            asyncio.run_coroutine_threadsafe(self._audio_callback(indata, frames, time, status), loop)

        async def process_audio_buffer_periodically():
            while self.running:
                await asyncio.sleep(0.05)  # Process buffer every 0.05 seconds (50ms)
                async with self.buffer_lock:
                    if self.audio_buffer.size > 0:
                        await self.event_bus.publish("asr_status_update", "Transcribing")
                        transcribed_text = self._transcribe_np(self.audio_buffer)
                        if transcribed_text:
                            logger.debug(f"ASR transcribed text: {transcribed_text}")
                            await self.event_bus.publish("transcription_received", transcribed_text)
                            await self.transcription_queue.put(transcribed_text) # Put into queue for get_transcription
                        self.audio_buffer = np.array([], dtype=np.float32)  # Clear the buffer
                        await self.event_bus.publish("asr_status_update", "Listening")
            logger.info("Audio processing task stopped.")

        self.audio_processing_task = asyncio.create_task(process_audio_buffer_periodically())

        try:
            blocksize = self.vad_frame_size * 2
            with sd.InputStream(callback=sync_audio_callback,
                                 channels=1, dtype='float32', samplerate=self.SAMPLE_RATE, blocksize=blocksize):
                logger.info("Microphone stream started. Say something!")
                await self.event_bus.publish("asr_ready", True)
                while self.running:
                    yield await self.transcription_queue.get()
        except asyncio.CancelledError:
            logger.info("Microphone stream cancelled.")
        except Exception as e:
            logger.error(f"An error occurred during audio streaming: {e}")
            await self.event_bus.publish("asr_status_update", "Error")
            raise
        finally:
            if self.audio_processing_task:
                self.audio_processing_task.cancel()
            self.running = False
            logger.info("Microphone stream stopped.")


    async def stop_listening(self):
        self.running = False
        if self.audio_processing_task:
            self.audio_processing_task.cancel()
            try:
                await self.audio_processing_task
            except asyncio.CancelledError:
                pass
        logger.info("ASRProcessor stopped listening.")
        await self.event_bus.publish("asr_status_update", "Stopped")

    async def get_transcription(self) -> str:
        # This method is designed to be called by an external consumer
        # It will return the latest full transcription from the queue
        if not self.transcription_queue.empty():
            return await self.transcription_queue.get()
        return ""