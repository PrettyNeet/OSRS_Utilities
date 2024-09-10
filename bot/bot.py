import os
from discord.ext import commands
from config.settings import BOT_PREFIX, INTENTS
from bot.utils.logger import setup_logging

# setup the logger
logger = setup_logging()


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=INTENTS)

    async def setup_hook(self):
        await self.load_extension("bot.commands.herb_profit")
        await self.load_extension("bot.commands.fish_profit")
        await self.load_extension("bot.commands.duel")
        logger.info("loaded all extensions/commands")


bot = MyBot()


@bot.event
async def on_ready():
    logger.info("Logged in as: %s", {bot.user})
    await bot.tree.sync()


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
