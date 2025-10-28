# pyvts Development Tutorial

This tutorial provides a guide for developers on how to use the `pyvts` library to interact with the VTube Studio API.

## 1. Introduction

`pyvts` is a Python library designed to facilitate communication with the VTube Studio API. It allows you to build plugins and scripts that can control VTube Studio, enabling features such as:
- Triggering hotkeys and expressions.
- Injecting custom tracking parameters.
- Monitoring model changes and other events.
- Reading and modifying model properties.

The library is asynchronous and built on `asyncio`, making it suitable for applications that require non-blocking communication.

## 2. Installation

To get started, you need to install the `pyvts` library. You can do this using `pip`:

```bash
pip install pyvts
```

## 3. Basic Usage

Here's a step-by-step guide to connecting to VTube Studio and performing basic actions.

### Step 1: Import aiofiles and pyvts

First, import the necessary library:

```python
import asyncio
import pyvts
```

### Step 2: Create a VTS Instance

Create an instance of the `vts` class. You can customize the host, port, and other settings if needed, but the defaults are usually sufficient for local development.

```python
# Default settings connect to localhost:8001
myvts = pyvts.vts()
```

### Step 3: Connect and Authenticate

The entire process is asynchronous, so you'll need to use `async` and `await`. The connection and authentication flow is as follows:

1.  **Connect**: Establish a WebSocket connection to VTube Studio.
2.  **Authenticate**: Request permission to control VTube Studio. The first time your plugin runs, a popup will appear in VTube Studio asking for permission. Once granted, a token is generated and saved, which will be used for future sessions.

Here is a basic `main` function to handle this:

```python
async def main():
    await myvts.connect()
    await myvts.request_authenticate_token() # First-time authentication
    await myvts.request_authenticate()       # Authenticate with the token

    # Your code to interact with VTS goes here

    await myvts.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Interacting with VTube Studio

Once authenticated, you can send requests to the VTube Studio API. Here are some common examples:

**Get a List of Hotkeys**

You can get a list of all available hotkeys for the currently loaded model. This is useful for finding the `hotkeyID` of an expression you want to trigger.

```python
async def get_hotkeys():
    hotkey_list_request = myvts.vts_request.requestGetHotkeysInCurrentModel()
    response = await myvts.request(hotkey_list_request)

    if response and 'data' in response and 'availableHotkeys' in response['data']:
        for hotkey in response['data']['availableHotkeys']:
            print(f"Hotkey Name: {hotkey.get('name')}, ID: {hotkey.get('hotkeyID')}")
```

**Trigger a Hotkey**

To trigger an expression or any other action, you use the `requestTriggerHotkey` method with the `hotkeyID` you want to activate.

```python
async def trigger_expression(hotkey_id: str):
    trigger_request = myvts.vts_request.requestTriggerHotkey(hotkey_id)
    await myvts.request(trigger_request)
    print(f"Triggered hotkey: {hotkey_id}")
```

## 4. Complete Example

Here is a complete example that connects to VTube Studio, finds a hotkey named "my-expression" (you should replace this with a real expression name in your model), and triggers it.

```python
import asyncio
import pyvts

async def main():
    # --- Connection and Authentication ---
    myvts = pyvts.vts()
    try:
        await myvts.connect()
        await myvts.request_authenticate_token()
        await myvts.request_authenticate()
    except Exception as e:
        print(f"Failed to connect or authenticate: {e}")
        return

    # --- Find the Hotkey ID for a specific expression ---
    expression_name_to_find = "my-expression"
    hotkey_id_to_trigger = None

    hotkey_list_request = myvts.vts_request.requestGetHotkeysInCurrentModel()
    response = await myvts.request(hotkey_list_request)

    if response and 'data' in response and 'availableHotkeys' in response['data']:
        for hotkey in response['data']['availableHotkeys']:
            if hotkey.get('name') == expression_name_to_find:
                hotkey_id_to_trigger = hotkey.get('hotkeyID')
                print(f"Found hotkey '{expression_name_to_find}' with ID: {hotkey_id_to_trigger}")
                break

    if not hotkey_id_to_trigger:
        print(f"Could not find a hotkey named '{expression_name_to_find}'.")
    else:
        # --- Trigger the Expression ---
        print(f"Triggering hotkey for '{expression_name_to_find}' in 3 seconds...")
        await asyncio.sleep(3)

        trigger_request = myvts.vts_request.requestTriggerHotkey(hotkey_id_to_trigger)
        await myvts.request(trigger_request)
        print("Hotkey triggered!")

    # --- Cleanly Disconnect ---
    await myvts.close()

if __name__ == "__main__":
    asyncio.run(main())
```

This tutorial covers the basics of getting started with `pyvts`. For more advanced features, such as subscribing to events or injecting custom parameters, refer to the official `pyvts` documentation and examples.
