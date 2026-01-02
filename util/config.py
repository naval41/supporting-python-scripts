import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    _config_cache = None

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """
        Load the consolidated configuration from config.json.
        """
        if cls._config_cache:
            return cls._config_cache

        paths = [
            Path("config.json"),
            Path("util/config.json"),
            Path("supporting-python-scripts/config.json"),
            Path(__file__).parent / "config.json",
            Path(__file__).parent.parent / "config.json"
        ]

        # Allow explicit override via env var only for the path of the file, not individual keys
        if os.getenv("CONFIG_JSON_PATH"):
            paths.insert(0, Path(os.getenv("CONFIG_JSON_PATH")))

        for path in paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        cls._config_cache = json.load(f)
                        return cls._config_cache
                except Exception as e:
                    print(f"Error loading config from {path}: {e}")
        
        print("Warning: config.json not found. Please create it based on config.json.example")
        return {}

    @staticmethod
    def load_aws_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get AWS configuration.
        """
        # If config_path provided (for backward compatibility or specific file loading), try to load it separately
        # But per new requirement, we should rely on main config.
        if config_path and Path(config_path).exists():
             try:
                 with open(config_path, 'r', encoding='utf-8') as f:
                     return json.load(f)
             except:
                 pass

        config = Config.load_config()
        return config.get("aws", {})

    @staticmethod
    def get_db_config() -> Dict[str, Any]:
        """
        Get Database configuration.
        """
        config = Config.load_config()
        return config.get("database", {})

    @staticmethod
    def get_email_config() -> Dict[str, Any]:
        """
        Get Email configuration.
        """
        config = Config.load_config()
        return config.get("email", {})
