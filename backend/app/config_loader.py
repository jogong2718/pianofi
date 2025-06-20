# backend/app/config_loader.py
import sys
import os
from pathlib import Path

def get_config():
    """Load config based on environment (Docker vs local)"""
    try:
        # Try Docker/installed package import first
        from pianofi_config.config import Config
        return Config
    except ImportError:
        # Fall back to local development import
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        from packages.pianofi_config.config import Config
        return Config

Config = get_config()