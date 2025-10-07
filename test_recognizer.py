import pytest
import os
import numpy as np
from unittest.mock import MagicMock, patch

# Adjust the import path based on your project structure
from voice_engine.recognizer import VoiceRecognition

# Mock the sherpa_onnx library
@pytest.fixture
def mock_sherpa_onnx():
    with patch('sherpa_onnx.OnlineRecognizer') as mock_recognizer_class:
        with patch('sherpa_onnx.OnlineRecognizer.from_transducer') as mock_from_transducer:
            mock_recognizer_instance = MagicMock()
            mock_recognizer_class.return_value = mock_recognizer_instance
            mock_from_transducer.return_value = mock_recognizer_instance

            mock_stream_instance = MagicMock()
            mock_recognizer_instance.create_stream.return_value = mock_stream_instance

            # Mock the result object
            mock_result = MagicMock()
            mock_result.text = "mocked transcription"
            mock_recognizer_instance.get_result.return_value = mock_result

            # Simulate is_ready and is_endpoint behavior
            mock_recognizer_instance.is_ready.side_effect = [True, False] # Ready once, then not
            mock_recognizer_instance.is_endpoint.return_value = True # Always an endpoint for simplicity

            yield mock_recognizer_class, mock_from_transducer, mock_recognizer_instance, mock_stream_instance

@pytest.fixture
def mock_download_utils():
    with patch('voice_engine.utils.download_and_extract') as mock_download:
        with patch('voice_engine.utils.check_and_extract_local_file') as mock_check_extract:
            # Simulate that local file is NOT found, so download_and_extract is called
            mock_check_extract.return_value = None
            mock_download.return_value = "/mock/model/dir" # Simulate successful download
            yield mock_download, mock_check_extract

# @pytest.mark.asyncio
# async def test_voice_recognition_init_and_transcribe(mock_sherpa_onnx, mock_download_utils):
#     mock_recognizer_class, mock_from_transducer, mock_recognizer_instance, mock_stream_instance = mock_sherpa_onnx
#     mock_download, mock_check_extract = mock_download_utils

#     model_dir = "/fake/model/path"
#     # Ensure the mocked model directory exists for os.path.isfile checks
#     # Initially, files don't exist, so download logic is triggered
#     with patch('os.path.isfile', return_value=False):
#         vr = VoiceRecognition(model_dir=model_dir)

#     # Assert that the model check/download was attempted
#     mock_check_extract.assert_called_once()
#     mock_download.assert_called_once()

#     # Assert that OnlineRecognizer.from_transducer was called with correct paths
#     mock_from_transducer.assert_called_once_with(
#         tokens=os.path.join(model_dir, "tokens.txt"),
#         encoder=os.path.join(model_dir, "encoder.onnx"),
#         decoder=os.path.join(model_dir, "decoder.onnx"),
#         joiner=os.path.join(model_dir, "joiner.onnx"),
#         num_threads=1,
#         sample_rate=16000,
#         feature_dim=80,
#         enable_endpoint_detection=True,
#         decoding_method="modified_beam_search",
#         provider="cpu", # Default provider in test
#         debug=False,
#     )

#     # Assert that a stream was created
#     mock_recognizer_instance.create_stream.assert_called_once()

#     # Test transcription
#     dummy_audio = np.random.rand(16000).astype(np.float32)
#     transcribed_text = vr.transcribe_np(dummy_audio)

#     # Assert that waveform was accepted and decoded
#     mock_stream_instance.accept_waveform.assert_called_once_with(16000, dummy_audio)
#     mock_recognizer_instance.decode_stream.assert_called_once_with(mock_stream_instance)
#     mock_recognizer_instance.get_result.assert_called_once_with(mock_stream_instance)

#     # Assert that the correct text was returned
#     assert transcribed_text == "mocked transcription"

#     # Assert that stream was reset after endpoint
#     mock_recognizer_instance.is_endpoint.assert_called_once_with(mock_stream_instance)
#     mock_recognizer_instance.reset.assert_called_once_with(mock_stream_instance)
