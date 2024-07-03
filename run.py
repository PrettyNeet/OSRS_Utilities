import os
from bot.bot import bot

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
