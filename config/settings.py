"""Configuration loader for runtime settings.

This module safely loads environment and YAML configuration and provides
minimal fallbacks for test/CI environments where dependencies (discord,
dotenv) may not be installed.
"""
from typing import Any, Dict
import os

# Safe imports with fallbacks
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None

try:
    import discord
except Exception:
    # Minimal fallback for tests where discord isn't installed
    class _DummyIntents:
        def __init__(self, **kwargs):
            pass

    class _DummyDiscord:
        Intents = _DummyIntents

    discord = _DummyDiscord()

try:
    import yaml
except Exception:
    yaml = None

# Load .env if present (no-op in CI if dotenv missing)
load_dotenv()

# Load YAML config safely
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
config: Dict[str, Any] = {}
if yaml is not None:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh) or {}
    except FileNotFoundError:
        config = {}
    except Exception:
        # Re-raise unexpected YAML errors to surface misconfiguration
        raise

# Expose commonly used settings with sensible defaults
BOT_PREFIX = config.get("bot_prefix", "!")
INTENTS = discord.Intents(**config.get("intents", {}))
HEADERS = config.get("headers", {})
CACHE_TTL = config.get("cache", {}).get("ttl_seconds", 30)
WEAPONS_DB_PATH = config.get("database", {}).get("weapons_db_path", "data/db/weapons.db")
