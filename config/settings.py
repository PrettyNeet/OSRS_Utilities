# Make dotenv and discord imports resilient when running in test/CI environments
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None

try:
    # Make dotenv and discord imports resilient when running in test/CI environments
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

    import yaml

    load_dotenv()

    # Load additional settings from config.yaml with safe defaults
    with open("config/config.yaml", "r") as file:
        config = yaml.safe_load(file) or {}

    BOT_PREFIX = config.get("bot_prefix", "!")
    INTENTS = discord.Intents(**config.get("intents", {}))
    HEADERS = config.get("headers", {})
    CACHE_TTL = config.get('cache', {}).get('ttl_seconds', 30)
    WEAPONS_DB_PATH = config.get('database', {}).get('weapons_db_path', "data/db/weapons.db")
