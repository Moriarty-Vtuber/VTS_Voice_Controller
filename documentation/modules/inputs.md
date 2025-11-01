# Inputs Module

The `inputs` module is responsible for handling all external inputs to the application. It is designed to be modular, using a factory pattern to create different input processors.

## Key Classes

### `InputProcessorFactory`
*   **Purpose**: A factory class responsible for creating instances of different input processors.
*   **Responsibilities**:
    *   Provides a static method `create_processor` that takes a type string (e.g., "voice", "test") and an `EventBus` instance.
    *   Decouples the `ApplicationCore` from the concrete implementations of input processors, making the system more modular and easier to extend with new input types in the future.

### `SherpaOnnxASRProcessor`
*   **Purpose**: The primary implementation of the `ASRProcessor` interface, using the `sherpa-onnx` library for real-time speech-to-text.
*   **Responsibilities**:
    *   Initializes the speech recognition model based on the selected language.
    *   Opens a stream from the selected microphone.
    *   Continuously listens for audio input and generates text transcriptions.
    *   Publishes `transcription_received` and `asr_status_update` events to the `EventBus`.

### `TestInputProcessor`
*   **Purpose**: A simple input processor used for testing purposes.
*   **Responsibilities**:
    *   Generates a pre-defined sequence of test phrases and publishes them as `transcription_received` events, allowing for testing of the core logic without live audio.

### `utils/device_utils.py`
*   **Purpose**: A collection of utility functions for discovering hardware devices.
*   **Responsibilities**:
    *   `get_audio_input_devices()`: Queries the system for available microphones.
