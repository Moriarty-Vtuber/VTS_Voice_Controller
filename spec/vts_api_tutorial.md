# VTube Studio API Development Tutorial

This tutorial provides a comprehensive guide for developers on how to interact with the VTube Studio API.

## 1. Introduction

The VTube Studio API allows developers to create plugins and scripts that can interact with and control the VTube Studio application. The API is based on a WebSocket server, which provides a real-time, bidirectional communication channel.

Key capabilities of the API include:
- Authenticating and authorizing plugins.
- Requesting data, such as model information, hotkeys, and tracking parameters.
- Triggering actions, like activating expressions and moving the model.
- Subscribing to events to receive real-time notifications.

## 2. Connecting to the API

The VTube Studio API runs on a WebSocket server, which defaults to `ws://localhost:8001`. You can connect to this server using any WebSocket client library.

**Important**: Before a plugin can connect, the user must enable "Allow Plugin API access" in the VTube Studio settings.

## 3. The API Request Structure

All communication with the API is done through JSON messages. Every request sent to the API must contain the following fields:

```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "MyRequestID",
    "messageType": "APIStateRequest"
}
```

- **`apiName`**: Must always be `"VTubeStudioPublicAPI"`.
- **`apiVersion`**: The API version you are targeting. Currently `"1.0"`.
- **`requestID`**: A unique identifier for your request. The response will include this same ID, allowing you to match responses to your requests.
- **`messageType`**: The type of request you are making.

## 4. Authentication Flow

Before you can use most of the API's features, your plugin must be authenticated. This is a two-step process.

### Step 1: Request an Authentication Token

First, you need to request a token. This is only required the first time your plugin connects. Once a token is granted, you should save it for future sessions.

**Request:**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "TokenRequest1",
    "messageType": "AuthenticationTokenRequest",
    "data": {
        "pluginName": "My Awesome Plugin",
        "pluginDeveloper": "My Name"
    }
}
```

When this request is sent, a popup will appear in VTube Studio asking the user to allow or deny access.

**Response (if allowed):**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "TokenRequest1",
    "messageType": "AuthenticationTokenResponse",
    "data": {
        "authenticationToken": "a-very-long-and-unique-token-string"
    }
}
```

You should save the `authenticationToken` for all future sessions.

### Step 2: Authenticate with the Token

For every new session (e.g., when your plugin starts or reconnects), you must authenticate using the token you received.

**Request:**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "AuthRequest1",
    "messageType": "AuthenticationRequest",
    "data": {
        "pluginName": "My Awesome Plugin",
        "pluginDeveloper": "My Name",
        "authenticationToken": "the-token-you-saved"
    }
}
```

**Response (if successful):**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "AuthRequest1",
    "messageType": "AuthenticationResponse",
    "data": {
        "authenticated": true,
        "reason": "Token valid."
    }
}
```

Once you receive `authenticated: true`, you can start making other API requests.

## 5. Common API Requests

Here are some of the most common requests you can make to the API.

### Get a List of Hotkeys

This request retrieves all hotkeys available for the currently loaded model.

**Request:**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "GetHotkeys",
    "messageType": "HotkeysInCurrentModelRequest"
}
```

**Response (shortened example):**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "GetHotkeys",
    "messageType": "HotkeysInCurrentModelResponse",
    "data": {
        "modelLoaded": true,
        "availableHotkeys": [
            {
                "name": "My Expression",
                "type": "ToggleExpression",
                "hotkeyID": "Hotkey-12345"
            },
            {
                "name": "Wave Animation",
                "type": "TriggerAnimation",
                "hotkeyID": "Hotkey-67890"
            }
        ]
    }
}
```

### Trigger a Hotkey

This is the primary way to make your model perform an action, such as changing an expression.

**Request:**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "TriggerHotkey1",
    "messageType": "HotkeyTriggerRequest",
    "data": {
        "hotkeyID": "Hotkey-12345"
    }
}
```

### Get Current Model Information

This request provides detailed information about the currently loaded model.

**Request:**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "GetModelInfo",
    "messageType": "CurrentModelRequest"
}
```

**Response (example):**
```json
{
    "apiName": "VTubeStudioPublicAPI",
    "apiVersion": "1.0",
    "requestID": "GetModelInfo",
    "messageType": "CurrentModelResponse",
    "data": {
        "modelLoaded": true,
        "modelName": "My Model",
        "modelID": "Model-abcde"
    }
}
```

This is particularly useful for detecting when a model has been changed, which is essential for dynamic plugins.

## 6. Subscribing to Events

The VTube Studio API allows you to subscribe to events to receive real-time notifications for various actions. This is more efficient than polling for changes.

For a detailed list of available events and how to subscribe to them, please refer to the official VTube Studio API documentation.

## 7. Further Reading

This tutorial covers only the basics of the VTube Studio API. For a complete list of all available requests, responses, and events, please consult the official documentation on the [VTube Studio GitHub repository](https://github.com/DenchiSoft/VTubeStudio).
