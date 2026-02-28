import os
from bot.bot import bot


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("DISCORD_BOT_TOKEN environment variable is required to run the bot")
    bot.run(token)
