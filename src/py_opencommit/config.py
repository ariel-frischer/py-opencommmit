"""Configuration module for py-opencommit."""

import json
import os
from pathlib import Path


def get_config_path():
    """Get the path to the config file."""
    config_dir = Path.home() / ".config" / "py-opencommit"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def get_config():
    """Get the configuration."""
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config):
    """Save the configuration."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return config