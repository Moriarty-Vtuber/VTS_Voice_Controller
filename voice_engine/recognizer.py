import os
import numpy as np
import sherpa_onnx
from loguru import logger
from .utils import download_and_extract, check_and_extract_local_file
import onnxruntime

class VoiceRecognition:
    def __init__(
        self,
        model_dir: str,
        decoding_method: str = "greedy_search",
        debug: bool = False,
        sample_rate: int = 16000,
        provider: str = "cpu",
    ) -> None:
        self.model_dir = model_dir
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

        self._check_and_download_model()
        self.recognizer = self._create_recognizer()
        self.stream = self.recognizer.create_stream()
        self.last_text = ""

    def _check_and_download_model(self):
        # Check for a key file to determine if the directory is valid.
        # For streaming zipformer, we expect encoder.onnx, decoder.onnx, joiner.onnx, tokens.txt
        expected_files = ["encoder.onnx", "decoder.onnx", "joiner.onnx", "tokens.txt"]
        all_files_exist = all(os.path.isfile(os.path.join(self.model_dir, f)) for f in expected_files)

        if not all_files_exist:
            logger.warning(f"Streaming Zipformer model not found in {self.model_dir}. Attempting to download and extract...")
            url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-en-20M-2023-02-17.tar.bz2"
            output_dir = os.path.dirname(self.model_dir)
            try:
                ensure_model_downloaded_and_extracted(url, output_dir)
                logger.info("Model download and extraction process completed.")
            except Exception as e:
                logger.error(f"Failed to download or extract model: {e}")
                raise

    def _create_recognizer(self):
        return sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=os.path.join(self.model_dir, "tokens.txt"),
            encoder=os.path.join(self.model_dir, "encoder.onnx"),
            decoder=os.path.join(self.model_dir, "decoder.onnx"),
            joiner=os.path.join(self.model_dir, "joiner.onnx"),
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
        
        current_text = self.recognizer.get_result(self.stream).text
        
        text_to_return = ""
        if current_text and current_text != self.last_text:
            text_to_return = current_text[len(self.last_text):].strip()
            self.last_text = current_text

        if self.recognizer.is_endpoint(self.stream):
            self.recognizer.reset(self.stream)
            self.last_text = ""

        return text_to_return

    async def async_transcribe_np(self, audio: np.ndarray) -> str:
        return self.transcribe_np(audio)