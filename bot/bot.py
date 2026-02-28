import os
import aiohttp
import discord
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
        from bot.utils.DButil import initialize_db, add_predefined_weapons, seed_items, seed_dummy_user
        initialize_db()
        add_predefined_weapons()
        seed_items()
        seed_dummy_user()

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
    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        # Dev mode: sync only to the target guild (appears instantly).
        # Also clear global commands so Discord doesn't show both sets.
        guild = discord.Object(id=int(guild_id))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        logger.info("Dev mode: commands synced to guild %s only (global cleared)", guild_id)
    else:
        await bot.tree.sync()
        logger.info("Synced slash commands globally (may take up to 1 hour to appear in Discord)")


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
