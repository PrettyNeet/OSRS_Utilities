# OSRS Utilities

This is a Discord bot that fetches the latest prices from the Old School Runescape Grand Exchange and calculates the potential profit from herb farming runs. More features soon.

## Features

- Fetches current Grand Exchange prices for herb seeds and grimy herbs.
- Calculates potential profit per herb farming run.
- Displays profit data in a nicely formatted table in Discord.

## Folder Structure

```bash
osrs_utilities/
├── bot/
│   ├── __init__.py
│   ├── bot.py
│   ├── commands.py
│   ├── utils.py
├── config/
│   ├── __init__.py
│   ├── config.yaml
│   ├── settings.py
├── data/
│   ├── __init__.py
│   ├── items.py
├── .env
├── .gitignore
├── LICENSE
├── README.md
└── run.py
```

## Setup

### Prerequisites

- Python 3.7+
- A Discord account and a Discord server where you have permission to add bots.

### Installation

1. __Clone the repository:__

    ```bash
    git clone https://github.com/PrettyNeet/OSRS_Utilities
    cd osrs_utilities
    ```

2. __Install dependencies:__

    ```bash
    pip install -r requirements.txt
    ```

3. __Set up environment variables:__

    Create a `.env` file in the root directory and add your Discord bot token:

    ```env
    DISCORD_BOT_TOKEN=your_discord_bot_token
    ```

4. __Configure settings:__

    Update `config.yaml` with any additional settings you need.

5. __Run the bot:__

    ```bash
    python run.py
    ```

## Usage

- Add your bot to your Discord server using the OAuth2 URL generated in the Discord Developer Portal.
- Use the `!herb_profit` command in your Discord server to see the profit data.

## Debugging

To enable or disable debugging, set the debug value in config/config.yaml:

```yaml
debug: true
```

When debugging is enabled, additional information will be printed to the console to help diagnose issues.

## Adding New Commands and Features

To add new commands and features, follow these steps:

1. __Create a new command file (optional):__

- If you have multiple commands related to a feature, you might want to group them in a separate file.
- For example, create a file bot/new_feature_commands.py.

2. __Define the command in the command file:__

- Implement the command as a class inheriting from commands.Cog.
- Register the command using the @commands.command() decorator.

3. __Add utility functions (if needed):__

- If the command requires helper functions, add them to bot/utils.py.

4. __Load the new command in run.py:__

- Ensure the new command file is imported and the setup function is called.

## Contributing

Feel free to submit issues or pull requests if you have any improvements or features you would like to add.

## License

This project is licensed under the MIT License.
