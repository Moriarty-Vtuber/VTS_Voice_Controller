import os
import numpy as np
import sherpa_onnx
from loguru import logger
import onnxruntime

class VoiceRecognition:
    def __init__(
        self,
        tokens_path: str,
        encoder_path: str,
        decoder_path: str,
        joiner_path: str,
        decoding_method: str = "greedy_search",
        debug: bool = False,
        sample_rate: int = 16000,
        provider: str = "cpu",
    ) -> None:
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
        self.last_text = ""

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

    def transcribe_np(self, audio: np.ndarray) -> str:
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

    async def async_transcribe_np(self, audio: np.ndarray) -> str:
        return self.transcribe_np(audio)