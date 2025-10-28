# VTS Voice Controller - Application Specification

## 1. Overview

This document provides a detailed technical specification for the VTS Voice Controller application. Its purpose is to serve as a guide for developers to understand the application's architecture, components, and data flow.

The application's primary function is to listen for voice commands from a user's microphone, interpret those commands, and trigger actions in VTube Studio, such as changing expressions on a Live2D model.

## 2. Core Architecture

The application is built on an asynchronous, event-driven architecture using Python's `asyncio` library. This allows for concurrent handling of tasks, such as listening for voice input, communicating with the VTube Studio API, and managing the user interface without blocking.

The core components are decoupled and communicate through an **Event Bus**, which is a central message-passing system that allows different parts of the application to interact without having direct dependencies on each other.

### Key Technologies
- **VTube Studio Communication**: `pyvts` library for WebSocket communication with the VTube Studio API.
- **Voice Recognition (ASR)**: `sherpa-onnx` for real-time, on-device speech-to-text processing.
- **Audio Input**: `sounddevice` for capturing microphone input.
- **GUI**: `PyQt6` for the user interface, with `qasync` to integrate with `asyncio`.
- **Configuration**: `pyyaml` for managing user settings.

## 3. Component Breakdown

The application is divided into several logical components:

### 3.1. Main Application (`vts_main.py`)
- **Purpose**: The entry point of the application.
- **Responsibilities**:
    - Initializes logging.
    - Sets up the `asyncio` event loop with `qasync` for `PyQt6`.
    - Creates and runs the main `AppUI`.

### 3.2. Application Core (`core/application_core.py`)
- **Purpose**: The central orchestrator of the application. It initializes and manages all other components.
- **Responsibilities**:
    - Manages the application's lifecycle (start, stop).
    - Initializes the `VTSWebSocketAgent`, `IntentResolver`, and the selected `InputProcessor`.
    - Contains the main asynchronous tasks that run the application.
    - Monitors for VTube Studio model changes and triggers UI updates.

### 3.3. Event Bus (`core/event_bus.py`)
- **Purpose**: A message-passing system for communication between components.
- **How it Works**:
    - Components can `subscribe` to specific event topics (e.g., `"transcription_received"`).
    - Other components can `publish` events to these topics.
    - This decouples the components, allowing for a more modular and testable architecture.

### 3.4. VTS WebSocket Agent (`agents/vts_output_agent.py`)
- **Purpose**: Handles all communication with the VTube Studio API.
- **Responsibilities**:
    - Connects, authenticates, and maintains the WebSocket connection.
    - Provides methods for making API requests (e.g., `get_hotkey_list`, `trigger_hotkey`).
    - Publishes events to the Event Bus based on API responses (e.g., `"vts_status_update"`).

### 3.5. Input Processors (`inputs/`)
- **Purpose**: Abstract interface for handling different types of input. The primary processor is for voice.

#### `asr_processor.py` (SherpaOnnxASRProcessor)
- **Purpose**: Listens to the microphone, performs speech-to-text, and publishes transcriptions.
- **Responsibilities**:
    - Initializes the `sherpa-onnx` recognizer.
    - Captures audio from the microphone using `sounddevice`.
    - Uses `webrtcvad` for voice activity detection (VAD) to identify speech.
    - Transcribes the speech and publishes the result to the `"transcription_received"` event topic.

### 3.6. Intent Resolver (`core/intent_resolver.py`)
- **Purpose**: Determines the user's intent based on the transcribed text.
- **How it Works**:
    - Subscribes to the `"transcription_received"` event.
    - When a transcription is received, it checks if any keywords from the user's configuration are present.
    - If a keyword is found, it publishes a `"hotkey_triggered"` event with the corresponding `hotkeyID`.

### 3.7. User Interface (`ui/`)
- **Purpose**: The graphical user interface for the application.

#### `app_ui.py` (AppUI)
- **Purpose**: The main controller for the UI. It connects the UI to the application core.
- **Responsibilities**:
    - Initializes the `MainWindow`.
    - Handles UI events (e.g., button clicks, dropdown selections).
    - Starts and stops the `ApplicationCore`.
    - Subscribes to events from the Event Bus to update the UI (e.g., displaying logs, updating status).

#### `main_window.py` (MainWindow)
- **Purpose**: Defines the layout and widgets of the main application window.
- **Responsibilities**:
    - Creates all UI elements (buttons, labels, dropdowns).
    - Populates the UI with data from the configuration file.
    - Provides methods for updating the UI (e.g., `append_log`, `set_status`).

## 4. Data Flow

Here is the typical data flow for a voice command:

1.  **Audio Input**: The `SherpaOnnxASRProcessor` captures audio from the microphone.
2.  **Transcription**: The audio is transcribed into text.
3.  **Event Published**: The `SherpaOnnxASRProcessor` publishes a `"transcription_received"` event to the Event Bus with the transcribed text as the payload.
4.  **Intent Resolution**: The `IntentResolver` receives the event, processes the text, and finds a matching keyword.
5.  **Hotkey Trigger**: The `IntentResolver` sends a request to the `VTSWebSocketAgent` to trigger the corresponding hotkey.
6.  **API Request**: The `VTSWebSocketAgent` sends the `HotkeyTriggerRequest` to the VTube Studio API.
7.  **Action in VTS**: VTube Studio receives the request and performs the action (e.g., activates an expression).

This event-driven flow ensures that each component has a single responsibility and that the system is easy to extend and maintain.
