import os
import aiohttp
from discord.ext import commands
from config.settings import BOT_PREFIX, INTENTS
from bot.utils.logger import setup_logging

# setup the logger
logger = setup_logging()


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=INTENTS)
        self.http_session: aiohttp.ClientSession | None = None

    async def setup_hook(self):
        # Create a shared aiohttp session for the bot to reuse
        if self.http_session is None:
            headers = {}
            try:
                from config.settings import HEADERS
                headers = HEADERS
            except Exception:
                headers = {}
            self.http_session = aiohttp.ClientSession(headers=headers)

        await self.load_extension("bot.commands.herb_profit")
        await self.load_extension("bot.commands.fish_profit")
        await self.load_extension("bot.commands.duel")
        logger.info("loaded all extensions/commands")

    async def close(self):
        # Close the aiohttp session when shutting down
        if self.http_session is not None:
            await self.http_session.close()
            self.http_session = None
        await super().close()


bot = MyBot()


@bot.event
async def on_ready():
    logger.info("Logged in as: %s", {bot.user})
    await bot.tree.sync()


@bot.tree.error
async def on_app_command_error(interaction, error):
    # Log the error and show a friendly ephemeral message to the user
    logger.exception("App command error: %s", error)
    try:
        await interaction.response.send_message("An unexpected error occurred. The incident has been logged.", ephemeral=True)
    except Exception:
        # If response already sent/acknowledged, use followup
        try:
            await interaction.followup.send("An unexpected error occurred. The incident has been logged.", ephemeral=True)
        except Exception:
            pass
