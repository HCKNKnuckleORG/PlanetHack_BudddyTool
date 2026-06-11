"""
Configuration management for PlanetHack
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import os


class Config:
    """Configuration manager"""

    def __init__(self, config_path: str = "config/config.yaml", env: str = "dev"):
        self.env = env
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        default_config: Dict[str, Any] = {
            "app": {"name": "PlanetHack", "version": "1.0.0", "theme": "80s_hacker"},
            "logging": {"level": "INFO", "file": "logs/planethack.log"},
            "modules": {
                "recon": {"enabled": True},
                "sql": {"enabled": True},
                "xss": {"enabled": True},
                "auth": {"enabled": True},
                "file_upload": {"enabled": True},
                "ssrf": {"enabled": True},
                "xxe": {"enabled": True},
                "deserialization": {"enabled": True},
                "api": {"enabled": True},
                "business_logic": {"enabled": True},
                "access_control": {"enabled": True},
                "session": {"enabled": True},
                "csrf": {"enabled": True},
                "request_smuggling": {"enabled": True},
                "cache": {"enabled": True},
            },
            "tools": {
                "nmap": {"path": "nmap"},
                "sqlmap": {"path": "sqlmap"},
                "dirsearch": {"path": "dirsearch"},
            },
            "gui": {
                "theme": "80s_hacker",
                "colors": {
                    "bg": "#000000",
                    "fg": "#00FF00",
                    "accent": "#00FFFF",
                    "warning": "#FFFF00",
                    "error": "#FF0000",
                },
            },
        }

        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                file_config = yaml.safe_load(f) or {}
                # Merge with defaults
                default_config.update(file_config)

        # VERSION file is source of truth (scripts/version.sh)
        version_file = self.config_path.parent.parent / "VERSION"
        if version_file.exists():
            ver = version_file.read_text().strip()
            if ver:
                if "app" not in default_config:
                    default_config["app"] = {}
                default_config["app"]["version"] = ver

        # Override with environment variables
        env_config = self._load_env_config()
        default_config.update(env_config)

        return default_config

    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config: Dict[str, Any] = {}

        if os.getenv("LOG_LEVEL"):
            config.setdefault("logging", {})["level"] = os.getenv("LOG_LEVEL")

        if os.getenv("ENV"):
            config["environment"] = os.getenv("ENV")

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split(".")
        value: Any = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
