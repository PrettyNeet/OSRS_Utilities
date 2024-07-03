import os
from bot.bot import bot

async def main():
    await bot.setup_hook()
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
