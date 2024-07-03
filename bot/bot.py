import os
import sys
from discord.ext import commands
from config.settings import BOT_PREFIX, INTENTS

# Ensure the project root is in the system path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=INTENTS)

    async def setup_hook(self):
        await self.load_extension("bot.commands.herb_profit")
        await self.load_extension("bot.commands.fish_profit")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

bot.run(os.getenv("DISCORD_BOT_TOKEN"))