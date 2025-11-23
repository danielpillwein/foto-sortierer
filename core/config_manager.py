import json
import logging
from pathlib import Path

class ConfigManager:
    DEFAULT_CONFIG = {
        "default_source_path": "",
        "default_destination_path": "",
        "thumbnail_cache_size": 500,
        "dupe_threshold": 5,
        "theme": "dark",
        "test_data_folder": ""
    }

    def __init__(self, config_path="data/config.json"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger("FotoSortierer.ConfigManager")
        self.config = self.load_config()

    def load_config(self):
        """Loads configuration from JSON file. Returns defaults on failure."""
        if not self.config_path.exists():
            self.logger.info(f"Config file not found at {self.config_path}. Creating defaults.")
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = self.DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading config: {e}. Using defaults.")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, config_data=None):
        """Saves current configuration to JSON file."""
        if config_data is None:
            config_data = self.config

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            self.config = config_data
            self.logger.info("Configuration saved.")
        except IOError as e:
            self.logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        """Retrieves a configuration value."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Sets a configuration value and saves immediately."""
        self.config[key] = value
        self.save_config()
