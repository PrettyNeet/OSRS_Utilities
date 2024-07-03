import os
from bot.bot import bot

#defines the async function to setup and start the bot
async def main():
    await bot.setup_hook()
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))

#checks to see if script is run directly
if __name__ == "__main__":
    import asyncio #asyncio to allow for async code to be run
    asyncio.run(main()) #running main as event loop
