
import asyncio
import yaml
from loguru import logger
import os
import sys

from core.event_bus import EventBus
from agents.vts_output_agent import VTSWebSocketAgent
from core.intent_resolver import KeywordIntentResolver

class ApplicationCore:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.event_bus = EventBus()
        self.config = self._load_config()
        self.vts_agent = None
        self.intent_resolver = None

    def _load_config(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        config_path = os.path.join(base_path, self.config_path)

        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found at {config_path}. Creating a default one.")
            default_config = {
                'vts_settings': {
                    'host': '127.0.0.1',
                    'port': 8001,
                    'token_file': os.path.join(base_path, 'vts_token.txt')
                },
                'expressions': {
                    'DefaultExpression.exp3.json': {
                        'name': 'DefaultExpression',
                        'keywords': ['hello'],
                        'cooldown_s': 60
                    }
                }
            }
            try:
                with open(config_path, 'w') as f:
                    yaml.safe_dump(default_config, f, default_flow_style=False, allow_unicode=True)
                logger.info("Default configuration created.")
                return default_config
            except Exception as e:
                logger.error(f"Error creating default configuration: {e}")
                return None
        else:
            try:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading configuration from {config_path}: {e}")
                return None

    async def _initialize_components(self):
        if not self.config:
            logger.error("Initialization failed: Configuration is not loaded.")
            return

        vts_settings = self.config['vts_settings']
        self.vts_agent = VTSWebSocketAgent(
            host=vts_settings['host'],
            port=vts_settings['port'],
            token_file=vts_settings['token_file'],
            event_bus=self.event_bus
        )

        await self.vts_agent.connect()
        await self.vts_agent.authenticate()

        expression_map = await self._synchronize_expressions()

        self.intent_resolver = KeywordIntentResolver(self.event_bus, expression_map)

    async def _synchronize_expressions(self):
        logger.info("Checking for expression updates from VTube Studio...")
        try:
            hotkey_list_response = await self.vts_agent.get_hotkey_list()
            if hotkey_list_response and 'data' in hotkey_list_response and 'availableHotkeys' in hotkey_list_response['data']:
                vts_expressions = [h for h in hotkey_list_response['data']['availableHotkeys'] if h.get('type') == 'ToggleExpression']

                yaml_expressions = self.config.get('expressions', {})
                new_yaml_expressions = {}
                updated = False

                # Map VTS hotkey IDs to their file names for quick lookup
                file_to_hotkey_id_map = {exp.get('file'): exp.get('hotkeyID') for exp in vts_expressions}

                for exp in vts_expressions:
                    exp_file = exp.get('file')
                    exp_name = exp.get('name')
                    if not exp_file or not exp_name:
                        continue

                    if exp_file in yaml_expressions: # Existing expression
                        # Preserve existing keywords and cooldown_s
                        new_yaml_expressions[exp_file] = yaml_expressions[exp_file]
                    else: # New expression from VTS
                        placeholder_keyword = f"NEW_KEYWORD_{exp_name.replace(' ', '_')}"
                        new_yaml_expressions[exp_file] = {
                            'name': exp_name,
                            'keywords': [placeholder_keyword],
                            'cooldown_s': 60 # Default cooldown
                        }
                        updated = True

                # Check for removed expressions (optional, but good practice)
                if len(new_yaml_expressions) != len(yaml_expressions):
                    updated = True

                if updated:
                    self.config['expressions'] = new_yaml_expressions
                    with open(self.config_path, 'w') as f:
                        yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                    logger.info(f"Successfully updated '{self.config_path}' with the latest expressions.")

                session_expression_map = {}
                # Build the session_expression_map from the updated config
                for exp_file, exp_data in new_yaml_expressions.items():
                    hotkey_id = file_to_hotkey_id_map.get(exp_file)
                    if hotkey_id:
                        for keyword in exp_data.get('keywords', []):
                            session_expression_map[keyword] = hotkey_id
                        # Also add the VTS expression name as a keyword
                        session_expression_map[exp_data['name']] = hotkey_id
                
                logger.info("Expression map created. Ready to detect keywords.")
                return session_expression_map

        except Exception as e:
            logger.error(f"Failed to auto-update expressions: {e}")
        return {}

    async def run(self):
        await self._initialize_components()
        if not self.vts_agent or not self.intent_resolver:
            logger.error("Application cannot start due to initialization failure.")
            return

        logger.info("Starting application components...")

        # --- Simulation task for testing ---
        async def simulate_and_shutdown():
            await asyncio.sleep(5) # Wait for everything to settle
            logger.warning("--- SIMULATING VOICE COMMAND ---")
            await self.event_bus.publish("transcription_received", "I am so angry")
            logger.warning("--- SIMULATION SENT ---")
            await asyncio.sleep(2) # Wait for processing
            logger.warning("--- SHUTTING DOWN APPLICATION ---")
            # Cancel all other tasks to gracefully exit
            current_task = asyncio.current_task()
            for task in asyncio.all_tasks():
                if task is not current_task:
                    task.cancel()

        tasks = [
            asyncio.create_task(self.intent_resolver.resolve_intent()),
            asyncio.create_task(self.vts_agent.run()),
            asyncio.create_task(simulate_and_shutdown()), # Add simulation and shutdown task
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Stopping application...")
        finally:
            for task in tasks:
                task.cancel()
            if self.vts_agent:
                await self.vts_agent.disconnect()
