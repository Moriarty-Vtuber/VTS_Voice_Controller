# Core Module

The `core` module is the central hub of the application, orchestrating the main logic and communication between different components. It is designed with a clear separation of concerns, with services dedicated to specific tasks.

## Key Classes

### `ApplicationCore`
*   **Purpose**: The main class that orchestrates the application's lifecycle. It acts as a coordinator, delegating tasks to specialized services.
*   **Responsibilities**:
    *   Initializes and manages the lifecycle of the `VTubeStudioService`, `ExpressionService`, and `KeywordIntentResolver`.
    *   Uses the `InputProcessorFactory` to create the appropriate ASR processor.
    *   Manages the main application `run` loop, gathering and coordinating the asyncio tasks.

### `ExpressionService`
*   **Purpose**: Handles all logic related to VTube Studio expressions.
*   **Responsibilities**:
    *   Fetching available expressions from the VTube Studio API via the `VTubeStudioService`.
    *   Comparing the VTS expressions with the local `vts_config.yaml`.
    *   Automatically updating the config file with new or removed expressions.
    *   Building the final, in-memory keyword-to-hotkey map used for intent resolution.

### `EventBus`
*   **Purpose**: A central messaging system that decouples the application's components.
*   **Responsibilities**:
    *   Allows components to subscribe to and publish events, enabling a modular architecture.

### `VTubeStudioService`
*   **Purpose**: A wrapper for the `pyvts` library that handles all direct communication with the VTube Studio API.
*   **Responsibilities**:
    *   Connecting, authenticating, and disconnecting from the VTube Studio API.
    *   Providing low-level methods for fetching hotkey lists and triggering hotkeys.

### `KeywordIntentResolver`
*   **Purpose**: Determines user intent from transcribed text.
*   **Responsibilities**:
    *   Subscribes to `transcription_received` events.
    *   Matches keywords against the map provided by the `ExpressionService`.
    *   Publishes `hotkey_triggered` events.

### `ConfigLoader`
*   **Purpose**: A robust utility class for loading and saving YAML configuration files.
*   **Responsibilities**:
    *   Gracefully handles missing files by returning a default empty dictionary, preventing crashes on first launch.
    *   Provides standardized methods for reading and writing YAML files.

### `interfaces.py`
*   **Purpose**: Defines abstract base classes (interfaces) for key components like `ASRProcessor`, ensuring a common API for different implementations.
