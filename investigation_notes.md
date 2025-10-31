# Investigation Notes

## Root Cause Analysis

The VTube Studio model does not react to keyword triggers because the `hotkey_triggered` event is not being handled by the `ApplicationCore` in a way that calls the `VTubeStudioService.trigger_hotkey` method.

The investigation revealed the following event flow:

1.  The `ASRProcessor` correctly transcribes audio and publishes a `transcription_received` event.
2.  The `KeywordIntentResolver` receives this event, detects a keyword, and publishes a `hotkey_triggered` event with the corresponding hotkey ID as the payload.
3.  The `AppUI` subscribes to the `hotkey_triggered` event in its `start_application` method. However, the event handler (`_handle_hotkey_events`) only appends the hotkey ID to the UI's log panel for display. It does not call the `VTubeStudioService.trigger_hotkey` method.

The `ApplicationCore` is responsible for managing the `VTubeStudioService` and should be responsible for triggering hotkeys. While it has a method for handling emotion-based triggers (`_handle_emotion_events`), it lacks a corresponding method for handling keyword-based hotkey triggers.

## VTube Studio API Verification

Research into the official VTube Studio API documentation confirms that the `HotkeyTriggerRequest` is the correct method for triggering hotkeys. The implementation in `core/vts_service.py`, which uses the `pyvts` library's `requestTriggerHotKey` method, is a correct and appropriate use of the API.

## Conclusion

The problem is not with the VTube Studio API usage, but with the application's internal event handling. The `hotkey_triggered` event is being consumed by the UI for logging purposes, but it is not being handled by the `ApplicationCore` to actually trigger the hotkey in VTube Studio.

## Detailed Solution Proposal

To fix this issue, I will implement a new method in `core/application_core.py` to handle the `hotkey_triggered` event and call the `VTubeStudioService.trigger_hotkey` method.

### `core/application_core.py`

#### **Before Change**

The `run` method in `ApplicationCore` does not have a task for handling hotkey events:

```python
    async def run(self):
        logger.debug("ApplicationCore.run() entered.")
        await self._initialize_components()

        if not self.input_processor:
            logger.error("No input processor was initialized. Aborting run.")
            return

        logger.info("Starting application components...")
        tasks = [
            asyncio.create_task(self.intent_resolver.resolve_intent()),
            asyncio.create_task(self._input_consumer()),
        ]

        if self.input_type == "emotion_detection":
            tasks.append(asyncio.create_task(self._handle_emotion_events()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Application tasks were cancelled.")
        finally:
            logger.info("Shutting down application components...")
            if self.vts_service:
                await self.vts_service.disconnect()
            if self.input_processor:
                if isinstance(self.input_processor, ASRProcessor):
                    await self.input_processor.stop_listening()
                elif isinstance(self.input_processor, EmotionProcessor):
                    await self.input_processor.stop_detection()
```

#### **After Change**

I will add a new method `_handle_hotkey_events` and a corresponding task in the `run` method:

```python
    async def _handle_hotkey_events(self):
        """Consumes hotkey triggered events and triggers VTS hotkeys."""
        hotkey_queue = await self.event_bus.subscribe("hotkey_triggered")
        while True:
            try:
                event = await hotkey_queue.get()
                hotkey_id = event.payload
                logger.info(f"Hotkey event received. Triggering VTube Studio hotkey: {hotkey_id}")
                await self.vts_service.trigger_hotkey(hotkey_id)
                hotkey_queue.task_done()
            except asyncio.CancelledError:
                logger.info("Hotkey event handler task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in hotkey event handler: {e}")

    async def run(self):
        logger.debug("ApplicationCore.run() entered.")
        await self._initialize_components()

        if not self.input_processor:
            logger.error("No input processor was initialized. Aborting run.")
            return

        logger.info("Starting application components...")
        tasks = [
            asyncio.create_task(self.intent_resolver.resolve_intent()),
            asyncio.create_task(self._input_consumer()),
            asyncio.create_task(self._handle_hotkey_events()),
        ]

        if self.input_type == "emotion_detection":
            tasks.append(asyncio.create_task(self._handle_emotion_events()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Application tasks were cancelled.")
        finally:
            logger.info("Shutting down application components...")
            if self.vts_service:
                await self.vts_service.disconnect()
            if self.input_processor:
                if isinstance(self.input_processor, ASRProcessor):
                    await self.input_processor.stop_listening()
                elif isinstance(self.input_processor, EmotionProcessor):
                    await self.input_processor.stop_detection()
```

### Expected Result

With these changes, the `ApplicationCore` will now listen for `hotkey_triggered` events and call the `vts_service.trigger_hotkey` method. This will cause the VTube Studio model to correctly trigger the expression associated with the detected keyword. The UI will continue to log the triggered event as before.
