from loguru import logger
from core.vts_service import VTubeStudioService
from core.config_loader import ConfigLoader


class ExpressionService:
    def __init__(self, vts_service: VTubeStudioService, config_path: str):
        self.vts_service = vts_service
        self.config_path = config_path
        self.config = ConfigLoader.load_yaml(config_path)

    async def synchronize_and_get_map(self) -> dict:
        """
        Orchestrates the full expression synchronization process.
        """
        logger.info("Synchronizing expressions with VTube Studio...")
        vts_expressions = await self._get_vts_expressions()

        if not vts_expressions:
            logger.warning(
                "No expressions found in VTube Studio. Using expressions from local config.")
            return self._build_session_expression_map(self.config.get('expressions', {}), [])

        yaml_expressions = self.config.get('expressions', {})
        updated_yaml_expressions = self._update_config_file(
            vts_expressions, yaml_expressions)

        return self._build_session_expression_map(updated_yaml_expressions, vts_expressions)

    async def _get_vts_expressions(self) -> list:
        """Fetches ToggleExpression hotkeys from VTube Studio."""
        if not self.vts_service or not self.vts_service.vts.get_connection_status():
            return []
        try:
            response = await self.vts_service.get_hotkey_list()
            return [h for h in response['data']['availableHotkeys'] if h.get('type') == 'ToggleExpression']
        except Exception as e:
            logger.error(f"Failed to get VTS expressions: {e}")
            return []

    def _update_config_file(self, vts_expressions: list, yaml_expressions: dict) -> dict:
        """
        Compares VTS expressions with local config, updates the config file if
        there are changes, and returns the updated expressions dictionary.
        """
        updated = False
        current_yaml = yaml_expressions.copy()
        vts_files = {exp.get('file') for exp in vts_expressions}

        for exp in vts_expressions:
            if exp.get('file') not in current_yaml:
                current_yaml[exp.get('file')] = {
                    'name': exp.get('name'),
                    'keywords': [f"KEYWORD_{exp.get('name', '').replace(' ', '_')}"],
                    'cooldown_s': 60
                }
                updated = True

        for file in list(current_yaml.keys()):
            if file not in vts_files:
                del current_yaml[file]
                updated = True

        if updated:
            self.config['expressions'] = current_yaml
            ConfigLoader.save_yaml(self.config_path, self.config)

        return current_yaml

    def _build_session_expression_map(self, yaml_expressions: dict, vts_expressions: list) -> dict:
        """Builds the in-memory map of keywords to hotkey data."""
        session_map = {}
        file_to_hotkey_id = {exp.get('file'): exp.get(
            'hotkeyID') for exp in vts_expressions}

        for exp_file, data in yaml_expressions.items():
            hotkey_id = file_to_hotkey_id.get(exp_file)
            if hotkey_id:
                for keyword in data.get('keywords', []):
                    session_map[keyword.lower()] = {
                        "hotkeyID": hotkey_id, "cooldown_s": data.get('cooldown_s', 60)}
        return session_map
