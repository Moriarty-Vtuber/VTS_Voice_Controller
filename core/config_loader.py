import yaml
from loguru import logger


class ConfigLoader:
    @staticmethod
    def load_yaml(file_path: str) -> dict:
        """
        Loads a YAML file and returns its content as a dictionary.
        If the file does not exist, it logs a warning and returns an empty dictionary.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config is not None else {}
        except FileNotFoundError:
            logger.warning(
                f"Configuration file not found: {file_path}. A new one will be created if needed.")
            return {}
        except Exception as e:
            logger.error(f"Failed to load YAML file {file_path}: {e}")
            return {}

    @staticmethod
    def save_yaml(file_path: str, data: dict):
        """
        Saves a dictionary to a YAML file.
        It will create the file if it doesn't exist.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, default_flow_style=False,
                               allow_unicode=True)
            logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save YAML file {file_path}: {e}")
