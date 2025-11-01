from loguru import logger
from core.event_bus import EventBus, Event
from core.vts_service import VTubeStudioService


class KeywordIntentResolver:
    def __init__(self, event_bus: EventBus, expression_map: dict):
        self.event_bus = event_bus
        self.expression_map = expression_map
        self.vts_service = VTubeStudioService
        self.active_cooldowns = {}
        logger.info(
            f"KeywordIntentResolver initialized with {len(expression_map)} keywords.")

    async def resolve_intent(self):
        transcription_queue = await self.event_bus.subscribe("transcription_received")
        while True:
            event = await transcription_queue.get()
            transcription = event.payload.lower()
            logger.debug(f"Received transcription: {transcription}")

            matched_keyword = self._find_matching_keyword(transcription)

            if matched_keyword:
                expression_data = self.expression_map[matched_keyword]
                hotkey_id = expression_data.get("hotkeyID")
                cooldown_s = expression_data.get("cooldown_s", 0)

                if self._is_hotkey_on_cooldown(hotkey_id):
                    logger.debug(
                        f"Hotkey {hotkey_id} is on cooldown. Skipping.")
                    continue

                logger.info(
                    f"Keyword '{matched_keyword}' matched. Triggering hotkey: {hotkey_id}")
                await self.event_bus.publish("hotkey_triggered", hotkey_id)

                if cooldown_s > 0:
                    self._start_cooldown(hotkey_id, cooldown_s)

    def _find_matching_keyword(self, transcription: str) -> str | None:
        """
        Finds the first matching keyword in the transcription.
        Returns the keyword string if found, otherwise None.
        """
        for keyword in self.expression_map.keys():
            if keyword in transcription:
                return keyword
        return None

    def _is_hotkey_on_cooldown(self, hotkey_id: str) -> bool:
        """
        Checks if a hotkey is currently on cooldown.
        """
        cooldown_end_time = self.active_cooldowns.get(hotkey_id)
        if cooldown_end_time and asyncio.get_event_loop().time() < cooldown_end_time:
            return True
        return False

    def _start_cooldown(self, hotkey_id: str, cooldown_s: int):
        """
        Starts a cooldown for a given hotkey.
        """
        cooldown_end_time = asyncio.get_event_loop().time() + cooldown_s
        self.active_cooldowns[hotkey_id] = cooldown_end_time
        logger.debug(
            f"Cooldown started for hotkey {hotkey_id}. Ends in {cooldown_s}s.")
