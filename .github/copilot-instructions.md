This repository is a small Discord bot that fetches Old School RuneScape Grand Exchange prices
and computes simple profit estimates for herb farming and fish cooking. The instructions below
give concise, practical guidance so an AI coding assistant can be immediately productive.

Core architecture (big picture)
- Entrypoint: `run.py` — async main that loads command extensions and starts the bot.
- Bot shell: `bot/bot.py` — defines `MyBot` and global setup (prefix, intents, sync).
- Commands: `bot/commands/*.py` — each command is a Cog using discord.py app_commands; examples:
  - `bot/commands/herb_profit.py` (interactive form + uses `bot.utils.calculations`)
  - `bot/commands/fish_profit.py` (uses `bot.utils.api`, formats results via `discord.ui.View`)
- Utilities: `bot/utils/*.py` — API fetching (`api.py`), calculation & domain logic (`calculations.py`), helpers (`helpers.py`).
- Data: `data/items.py` — canonical mapping of item ids (seed_id, herb_id, raw/cooked ids) used by commands.
- Config: `config/config.yaml` + `config/settings.py` — load headers, intents, debug flag and BOT_PREFIX.

Why things are structured this way
- Commands are implemented as Cogs and loaded as extensions to keep the bot core minimal and make new features pluggable.
- Price fetching is centralized in `bot/utils/api.py` so commands use a single source of truth for price shape (the wiki API returns dicts keyed by item id strings).
- Calculation logic is intentionally separated to `calculations.py` so it can be reused/tested independently from Discord I/O.

Developer workflows and commands
- Run locally (requires Python and `.env` with `DISCORD_BOT_TOKEN`):
  - Install deps: `pip install -r requirements.txt`
  - Start: `python run.py` (this calls `bot.setup_hook()` and starts the bot)
- Docker: `docker-compose up --build` (project includes Dockerfile / docker-compose.yml)
- Configuration: edit `config/config.yaml` for `HEADERS`, `bot_prefix`, `intents`, `debug`.
- Debugging: set `debug: true` in `config/config.yaml` — code prints intermediate price and calculation values (see `calculations.py` and `herb_profit.py`).

Project-specific conventions & patterns
- Price dict shape: API returns data keyed by item id strings. Commands convert ints to strings before lookup, e.g. `prices[str(item_id)]["high"]` or `"avgHighPrice"` for 1h averages.
- Price type selection: commands accept `price_type` choices (`latest` => `high`, `1h` => `avgHighPrice`) — follow this mapping when adding features.
- Views & formatting: interactive responses use `discord.ui.View` with a select menu to choose output format (`markdown` or `embed`). Keep UI code in the command module and call shared calc functions.
- Tests: minimal tests exist under `tests/` (currently a placeholder). Keep calculation logic pure and add unit tests for functions in `bot/utils/calculations.py` and `bot/utils/helpers.py`.

Integration points & external dependencies
- External API: https://prices.runescape.wiki/api/v1/osrs/latest and `/1h`. `bot/utils/api.py` sets `HEADERS` from `config/config.yaml` to satisfy the wiki's user-agent requirement.
- Environment: `DISCORD_BOT_TOKEN` must be present in `.env` for local runs or in the container environment for Docker.
- Libraries: `discord.py`, `requests`, `pandas` (used for tabular formatting in commands), `python-dotenv`, `pyyaml`.

Concrete examples & actionable tips for code edits
- Adding a new command: create `bot/commands/<name>.py`, implement a Cog with an `@app_commands.command`, call shared functions in `bot/utils/*`, and add an async `setup(bot)` that adds the cog.
- Fetch prices once per command invocation: call `fetch_latest_prices()` or `fetch_1h_prices()` in the command handler and pass the resulting dict (not individual ids) into calculation helpers.
- Respect price_key mapping: use `price_key = "high"` for `latest`, `price_key = "avgHighPrice"` for `1h` and access prices as `prices[str(item_id)][price_key]`.
- Avoid network in unit tests: mock `bot.utils.api.fetch_latest_prices()` and `fetch_1h_prices()`; test `calculate_custom_profit()` purely with synthetic price dicts.

Files to inspect first when debugging or extending
- `run.py`, `bot/bot.py`, `bot/commands/herb_profit.py`, `bot/commands/fish_profit.py`, `bot/utils/api.py`, `bot/utils/calculations.py`, `data/items.py`, `config/config.yaml`.

When in doubt, preserve these invariants
- Price data passed around should remain the original API data shape (dict keyed by id strings).
- Calculation helpers must not perform I/O; keep side-effects (sending messages, creating views) inside command modules.

If anything here is unclear or you want examples for a specific change (new command, test, or CI step), tell me which area to expand.
