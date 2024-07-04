from dotenv import load_dotenv
import discord
import yaml

load_dotenv()

# Load additional settings from config.yaml
with open("config/config.yaml", "r") as file:
    config = yaml.safe_load(file)

BOT_PREFIX = config["bot_prefix"]
INTENTS = discord.Intents(**config["intents"])
HEADERS = config["headers"]

DEBUG = config.get("debug", False)
