
# VTube Studio API Documentation

This document provides a comprehensive overview of the VTube Studio API, based on the information in the official VTube Studio GitHub repository.

## Table of Contents

- [VTube Studio API Documentation](#vtube-studio-api-documentation)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
  - [2. API Basics](#2-api-basics)
    - [2.1. WebSocket Connection](#21-websocket-connection)
    - [2.2. API Server Discovery (UDP)](#22-api-server-discovery-udp)
    - [2.3. Authentication](#23-authentication)
    - [2.4. Requests and Responses](#24-requests-and-responses)
  - [3. Permissions](#3-permissions)
    - [3.1. Requesting Permissions](#31-requesting-permissions)
    - [3.2. Available Permissions](#32-available-permissions)
  - [4. Events](#4-events)
    - [4.1. Subscribing and Unsubscribing](#41-subscribing-and-unsubscribing)
    - [4.2. Available Events](#42-available-events)
      - [4.2.1. TestEvent](#421-testevent)
      - [4.2.2. ModelLoadedEvent](#422-modelloadedevent)
      - [4.2.3. TrackingStatusChangedEvent](#423-trackingstatuschangedevent)
      - [4.2.4. BackgroundChangedEvent](#424-backgroundchangedevent)
      - [4.2.5. ModelConfigChangedEvent](#425-modelconfigchangedevent)
      - [4.2.6. ModelMovedEvent](#426-modelmovedevent)
      - [4.2.7. ModelOutlineEvent](#427-modeloutlineevent)
      - [4.2.8. HotkeyTriggeredEvent](#428-hotkeytriggeredevent)
      - [4.2.9. ModelAnimationEvent](#429-modelanimationevent)
      - [4.2.10. ItemEvent](#4210-itemevent)
      - [4.2.11. ModelClickedEvent](#4211-modelclickedevent)
      - [4.2.12. PostProcessingEvent](#4212-postprocessingevent)
      - [4.2.13. Live2DCubismEditorConnectedEvent](#4213-live2dcubismeditorconnectedevent)
  - [5. API Requests](#5-api-requests)
  - [6. Data Structures](#6-data-structures)
    - [6.1. Error IDs (`ErrorID.cs`)](#61-error-ids-erroridcs)
    - [6.2. Hotkey Actions (`HotkeyAction.cs`)](#62-hotkey-actions-hotkeyactioncs)
    - [6.3. Restricted Raw Keys (`RestrictedRawKey.cs`)](#63-restricted-raw-keys-restrictedrawkeycs)
    - [6.4. Effects (`Effects.cs`)](#64-effects-effectscs)
    - [6.5. Effect Configurations (`EffectConfigs.cs`)](#65-effect-configurations-effectconfigscs)

## 1. Introduction

The VTube Studio API allows you to create plugins and scripts that can interact with VTube Studio. You can trigger hotkeys, control model parameters, react to events, and much more. This documentation provides a summary of the information found in the official VTube Studio GitHub repository.

## 2. API Basics

### 2.1. WebSocket Connection

The VTube Studio API is accessed through a WebSocket connection. The default WebSocket server address is `ws://localhost:8001`. The port can be changed by the user in the VTube Studio application.

### 2.2. API Server Discovery (UDP)

VTube Studio broadcasts its API state on the local network via UDP on port `47779`. This allows for automatic discovery of the VTube Studio API server.

### 2.3. Authentication

To use the API, you must first authenticate your plugin. This is a two-step process:

1.  **Request a token:** Send an `AuthenticationTokenRequest` with your plugin's name and developer name. The user will be prompted in VTube Studio to allow or deny access. If allowed, you will receive an authentication token.
2.  **Authenticate with the token:** Send an `AuthenticationRequest` with the received token, your plugin name, and developer name. This will authenticate your plugin for the current session.

The authentication token should be stored by your plugin and can be reused for future sessions.

### 2.4. Requests and Responses

All communication with the API is done through JSON messages. Each request must contain the `apiName` ("VTubeStudioPublicAPI") and `apiVersion` ("1.0"). You can also include a `requestID` to identify responses to your requests.

## 3. Permissions

Certain API functionalities require special permissions from the user.

### 3.1. Requesting Permissions

Permissions can be requested using the `PermissionRequest`. The user will be prompted to grant or deny the requested permission. Once a permission is granted, it can be revoked by the user at any time in the VTube Studio settings.

### 3.2. Available Permissions

*   `LoadCustomImagesAsItems`: Allows the plugin to load custom PNG/JPG data as items in VTube Studio.

## 4. Events

The VTube Studio API provides an event system that allows your plugin to be notified when certain actions occur.

### 4.1. Subscribing and Unsubscribing

To receive events, you must subscribe to them using the `EventSubscriptionRequest`. You can also unsubscribe from events using the same request.

### 4.2. Available Events

Here is a list of the available events and a brief description of each:

#### 4.2.1. TestEvent

An event for testing the event API.

#### 4.2.2. ModelLoadedEvent

Triggered when a VTube Studio model is loaded or unloaded.

#### 4.2.3. TrackingStatusChangedEvent

Triggered when the face tracker finds or loses the face or hands.

#### 4.2.4. BackgroundChangedEvent

Triggered when the background is changed.

#### 4.2.5. ModelConfigChangedEvent

Triggered when the settings of the currently loaded model are changed.

#### 4.2.6. ModelMovedEvent

Triggered when a model is moved, resized, or rotated.

#### 4.2.7. ModelOutlineEvent

Triggered at a constant 15 FPS and sends the model outline.

#### 4.2.8. HotkeyTriggeredEvent

Triggered when a hotkey is activated.

#### 4.2.9. ModelAnimationEvent

Triggered when an animation starts, ends, or a custom event is encountered.

#### 4.2.10. ItemEvent

Triggered for various item-related actions like adding, removing, clicking, etc.

#### 4.2.11. ModelClickedEvent

Triggered when the model is clicked.

#### 4.2.12. PostProcessingEvent

Triggered when the post-processing system is turned on/off or a preset is loaded/unloaded.

#### 4.2.13. Live2DCubismEditorConnectedEvent

Triggered when VTube Studio connects or disconnects from the Live2D Cubism Editor.

## 5. API Requests

The VTube Studio API provides a wide range of requests for controlling the application. For a detailed list of all requests and their parameters, please refer to the official `README.md` in the VTube Studio GitHub repository.

## 6. Data Structures

The following sections provide an overview of the enums and data structures used in the VTube Studio API.

### 6.1. Error IDs (`ErrorID.cs`)

This file contains a comprehensive list of all possible error IDs and their meanings. This is crucial for handling errors in your plugin.

### 6.2. Hotkey Actions (`HotkeyAction.cs`)

This file defines the different types of actions that can be triggered by hotkeys.

### 6.3. Restricted Raw Keys (`RestrictedRawKey.cs`)

This file contains a list of raw key codes that are supported as hotkeys in VTube Studio.

### 6.4. Effects (`Effects.cs`)

This file lists all the post-processing effects available in VTube Studio.

### 6.5. Effect Configurations (`EffectConfigs.cs`)

This file contains a large enum with all the post-processing effect configurations, including their types, ranges, and default values.
