# VTS Voice Controller

A Python application that controls your VTube Studio model's expressions using real-time voice recognition. It listens to your microphone, transcribes your speech, and triggers facial expressions in VTube Studio when specific keywords are detected.

This document provides a detailed overview of the project's architecture, data flow, and technologies, intended to help developers understand the system's inner workings.

## Features

- **Real-time Voice Recognition**: Listens to your microphone and transcribes speech locally.
- **Keyword-Based Expression Triggering**: Triggers expressions in VTube Studio when specific keywords are detected.
- **Automatic Expression Sync**: On startup, automatically discovers expressions from your VTube Studio model and updates the configuration file.
- **Flexible Keyword System**: Supports both custom keywords from the config file and the expression names from VTube Studio.
- **Spam Prevention**: Prevents the same expression from being spammed by enforcing a cooldown if triggered twice consecutively.
- **GPU Acceleration**: Can leverage a CUDA-enabled GPU for faster transcription if `onnxruntime-gpu` is installed.

## Architecture & Core Technologies

This project uses an asynchronous, event-driven architecture. The main components and the technologies they use are outlined below.

| Component                  | Technology / Library | Key File(s)                               | Description                                                                                             |
| -------------------------- | -------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **VTS Communication**      | [`pyvts`](https://github.com/Genteki/pyvts) | `vts_client.py`                           | Handles all communication with the VTube Studio API, including connection, authentication, and hotkey requests. Uses `asyncio.Lock` to prevent API request race conditions. |
| **Voice Recognition (ASR)**| `sherpa-onnx`        | `voice_engine/recognizer.py`              | A wrapper for the `sherpa-onnx` real-time speech-to-text engine. It processes audio data and returns transcribed text. |
| **Audio Input**            | `sounddevice`        | `vts_main.py`                             | Captures live audio from the default microphone into a buffer for processing.                                   |
| **Configuration**          | `pyyaml`             | `vts_config.yaml`, `vts_main.py`          | Manages application settings, including VTS connection details and keyword-to-expression mappings.      |
| **Asynchronous Execution** | `asyncio`            | `vts_main.py`, `vts_client.py`            | The foundation of the application, managing concurrent operations like audio processing and API calls without blocking. |
| **Logging**                | `loguru`             | `vts_main.py`                             | Provides robust and configurable logging to a file (`vts_controller.log`).                                |
| **Model Management**       | `requests`, `tqdm`   | `voice_engine/utils.py`                   | Downloads and extracts the required `sherpa-onnx` ASR models on the first run.                            |

## Detailed Application Flow

The application follows a clear, sequential flow from initialization to real-time operation.

### 1. Initialization (`vts_main.py`)
- The `main` function in `vts_main.py` is the entry point.
- It loads settings from `vts_config.yaml`. If the file doesn't exist, a default one is created.
- `loguru` is configured to write logs to `vts_controller.log`.

### 2. ASR Engine Setup (`vts_main.py` -> `voice_engine/`)
- The application checks if the `sherpa-onnx` model is present in the `models/` directory.
- If not, `voice_engine.utils.ensure_model_downloaded_and_extracted` downloads and extracts the model files.
- An instance of `VoiceRecognition` is created from `voice_engine/recognizer.py`. This class loads the ONNX model and prepares the `sherpa_onnx.OnlineRecognizer` for transcription.

### 3. VTube Studio Connection (`vts_main.py` -> `vts_client.py`)
- An instance of `VTSClient` is created.
- It connects to the VTube Studio API via WebSocket and performs authentication. The authentication token is stored in `vts_token.txt` by default.

### 4. Expression Synchronization (`vts_main.py`)
- The application sends a request to VTS to get a list of all available hotkeys for the current model.
- It filters this list to find hotkeys of type `ToggleExpression`.
- It then compares this list with the expressions in `vts_config.yaml`.
  - If an expression from VTS is not in the config file, it's added with a placeholder keyword (e.g., `NEW_KEYWORD_MyExpression`).
  - The `vts_config.yaml` file is updated on disk.
- Finally, an in-memory `expression_map` is built. This dictionary maps both the user-defined keywords and the VTS expression names to their corresponding `hotkeyID`. This allows for flexible keyword detection.

### 5. Audio Processing and Transcription (`vts_main.py`)
This is the core real-time loop of the application.
1.  **Audio Capture**: An `sd.InputStream` from the `sounddevice` library is opened. It continuously captures audio from the microphone in small chunks.
2.  **Buffering**: A callback function (`audio_callback`) is triggered for each audio chunk. This function appends the incoming audio data (a NumPy array) to a global `audio_buffer`. Access to this buffer is managed by an `asyncio.Lock` to prevent race conditions.
3.  **Periodic Processing**: A separate asynchronous task, `process_audio_buffer_periodically`, runs every 0.5 seconds.
4.  **Transcription**: This task takes the current `audio_buffer`, sends it to the `asr_engine.transcribe_np` method, and then clears the buffer. The `transcribe_np` method in `voice_engine/recognizer.py` feeds the audio into the `sherpa-onnx` engine, which returns the transcribed text if speech is detected.

### 6. Keyword Matching & Expression Triggering (`vts_main.py`)
1.  **Callback**: The transcribed text is passed to the `asr_callback` function.
2.  **Keyword Search**: The function converts the text to lowercase and iterates through the `expression_map` to see if any keyword is present.
3.  **Spam Prevention**: If a keyword is found, the system checks if the expression is on cooldown. An expression is put on a 60-second cooldown if it's triggered twice in a row.
4.  **Trigger**: If the expression is not on cooldown, `vts_client.trigger_expression` is called with the `hotkeyID`. This sends the final request to the VTube Studio API to activate the expression.

## Project Structure

```
F:\VTS_Voice_Controller/
├── vts_main.py             # Main application entry point, orchestrates all components.
├── vts_client.py           # Client for all VTube Studio API interactions.
├── vts_config.yaml         # Configuration file for VTS settings and expression keywords.
├── voice_engine/
│   ├── recognizer.py       # Wrapper for the sherpa-onnx ASR engine.
│   └── utils.py            # Utilities for downloading and managing ASR models.
├── models/                 # Directory where ASR models are stored (created automatically).
├── requirements.txt        # Python dependencies.
├── run.bat / run.sh        # Convenience scripts for running the application.
└── README.md               # This file.
```

## Setup and Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd VTS_Voice_Controller
    ```

2.  **Create a Python Virtual Environment**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Environment**
    -   On Windows: `.\.venv\Scripts\activate`
    -   On macOS/Linux: `source .venv/bin/activate`

4.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: For GPU support, you may need to manually install a specific version of `onnxruntime-gpu`)*

## Running the Application

This project includes convenient scripts to run the application.

-   **On Windows (Command Prompt/PowerShell):**
    ```cmd
    .\run.bat
    ```
-   **On macOS/Linux (or Git Bash on Windows):**
    ```sh
    ./run.sh
    ```
    *(You may need to make the `.sh` script executable first: `chmod +x run.sh`)*

Alternatively, you can run the program manually after activating the virtual environment:
```bash
python vts_main.py
```
On the first run, you will need to allow the plugin's authentication request inside VTube Studio. The ASR model will also be downloaded, which may take a few minutes.