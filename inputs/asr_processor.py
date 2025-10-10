
import asyncio
import sounddevice as sd
import numpy as np
import sherpa_onnx
from loguru import logger
import onnxruntime

from core.interfaces import InputProcessor
from core.event_bus import EventBus

class ASRProcessor(InputProcessor):
    def __init__(
        self,
        event_bus: EventBus,
        tokens_path: str,
        encoder_path: str,
        decoder_path: str,
        joiner_path: str,
        decoding_method: str = "greedy_search",
        debug: bool = False,
        sample_rate: int = 16000,
        provider: str = "cpu",
    ) -> None:
        self.event_bus = event_bus
        self.tokens_path = tokens_path
        self.encoder_path = encoder_path
        self.decoder_path = decoder_path
        self.joiner_path = joiner_path
        self.decoding_method = decoding_method
        self.debug = debug
        self.SAMPLE_RATE = sample_rate
        self.provider = provider

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
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_lock = asyncio.Lock()

    def _create_recognizer(self):
        return sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=self.tokens_path,
            encoder=self.encoder_path,
            decoder=self.decoder_path,
            joiner=self.joiner_path,
            num_threads=1,
            sample_rate=self.SAMPLE_RATE,
            feature_dim=80,
            enable_endpoint_detection=True,
            decoding_method=self.decoding_method,
            provider=self.provider,
            debug=self.debug,
        )

    def _transcribe_np(self, audio: np.ndarray) -> str:
        self.stream.accept_waveform(self.SAMPLE_RATE, audio)
        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)
        
        text_to_return = ""
        if self.recognizer.is_endpoint(self.stream):
            result = self.recognizer.get_result(self.stream)
            if isinstance(result, str):
                text_to_return = result.strip()
            else:
                text_to_return = result.text.strip()
            self.recognizer.reset(self.stream)

        return text_to_return

    async def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(status)
        async with self.buffer_lock:
            self.audio_buffer = np.concatenate((self.audio_buffer, indata.flatten()))

    async def process_input(self):
        logger.info("Starting microphone stream...")
        loop = asyncio.get_running_loop()

        def sync_audio_callback(indata, frames, time, status):
            asyncio.run_coroutine_threadsafe(self._audio_callback(indata, frames, time, status), loop)

        async def process_audio_buffer_periodically():
            while True:
                await asyncio.sleep(0.5)  # Process buffer every 0.5 seconds
                async with self.buffer_lock:
                    if self.audio_buffer.size > 0:
                        transcribed_text = self._transcribe_np(self.audio_buffer)
                        if transcribed_text:
                            await self.event_bus.publish("transcription_received", transcribed_text)
                        self.audio_buffer = np.array([], dtype=np.float32)  # Clear the buffer

        audio_processing_task = asyncio.create_task(process_audio_buffer_periodically())

        try:
            blocksize = int(self.SAMPLE_RATE * 0.2) # 200ms chunks
            with sd.InputStream(callback=sync_audio_callback,
                                 channels=1, dtype='float32', samplerate=self.SAMPLE_RATE, blocksize=blocksize):
                logger.info("Microphone stream started. Say something!")
                await audio_processing_task
        except Exception as e:
            logger.error(f"An error occurred during audio streaming: {e}")
            audio_processing_task.cancel()
            raise
