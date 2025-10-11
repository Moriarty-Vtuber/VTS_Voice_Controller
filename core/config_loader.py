
import yaml
from typing import Any, Dict
from loguru import logger

class ConfigLoader:
    """
    A utility class for loading configurations from YAML files.
    """

    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """
        Loads a YAML file and returns its content as a dictionary.

        Args:
            file_path: The path to the YAML file.

        Returns:
            A dictionary containing the configuration.
            Returns an empty dictionary if the file cannot be read or parsed.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            return {}
