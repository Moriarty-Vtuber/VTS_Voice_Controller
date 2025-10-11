
import asyncio
import time
from loguru import logger

from core.interfaces import IntentResolver
from core.event_bus import EventBus

class KeywordIntentResolver(IntentResolver):
    def __init__(self, event_bus: EventBus, expression_map: dict):
        self.event_bus = event_bus
        self.expression_map = expression_map
        self.last_triggered_expression = None
        self.consecutive_trigger_count = 0
        self.expression_cooldowns = {}

    async def _process_one_event(self, transcribed_text: str):
        if not transcribed_text:
            return

        logger.info(f"Transcribed: {transcribed_text}")
        lower_transcribed_text = transcribed_text.lower()

        for keyword, trigger_data in self.expression_map.items():
            if keyword.lower() in lower_transcribed_text:
                hotkey_id = trigger_data["hotkeyID"]
                cooldown_duration = trigger_data["cooldown_s"]

                if hotkey_id in self.expression_cooldowns and time.time() < self.expression_cooldowns[hotkey_id]:
                    remaining = self.expression_cooldowns[hotkey_id] - time.time()
                    logger.info(f"Keyword '{keyword}' detected, but expression {hotkey_id} is on cooldown for {remaining:.1f} more seconds.")
                    continue

                if hotkey_id == self.last_triggered_expression:
                    self.consecutive_trigger_count += 1
                else:
                    self.last_triggered_expression = hotkey_id
                    self.consecutive_trigger_count = 1

                if self.consecutive_trigger_count == 2:
                    self.expression_cooldowns[hotkey_id] = time.time() + cooldown_duration
                    logger.warning(f"Expression {hotkey_id} triggered twice consecutively. Placing on cooldown for {cooldown_duration} seconds.")

                logger.info(f"Keyword '{keyword}' detected. Triggering expression: {hotkey_id}")
                await self.event_bus.publish("hotkey_triggered", hotkey_id)

    async def resolve_intent(self):
        transcription_queue = await self.event_bus.subscribe("transcription_received")
        while True:
            event = await transcription_queue.get()
            await self._process_one_event(event.payload)
            transcription_queue.task_done()
