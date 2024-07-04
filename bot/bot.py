import os
from discord.ext import commands
from config.settings import BOT_PREFIX, INTENTS


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=INTENTS)

    async def setup_hook(self):
        await self.load_extension("bot.commands.herb_profit")
        await self.load_extension("bot.commands.fish_profit")
        await self.load_extension("bot.commands.duel")


bot = MyBot()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
