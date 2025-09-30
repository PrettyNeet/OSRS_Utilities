import os
from bot.bot import bot


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("DISCORD_BOT_TOKEN environment variable is required to run the bot")
    # `bot.run` is the convenient entrypoint; `setup_hook` will prepare the session and load extensions
    # Add graceful shutdown handling when running directly
    import signal
    import asyncio

    loop = asyncio.get_event_loop()

    def _shutdown_handler(*_args):
        loop.create_task(bot.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown_handler)
        except NotImplementedError:
            # add_signal_handler may not be implemented on Windows event loop
            pass

    bot.run(token)
