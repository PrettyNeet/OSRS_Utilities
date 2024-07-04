# OSRS Utilities

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

![GitHub last commit](https://img.shields.io/github/last-commit/PrettyNeet/OSRS_Utilities) ![GitHub commit activity](https://img.shields.io/github/commit-activity/m/PrettyNeet/OSRS_Utilities) 

This Discord bot fetches the latest prices from the Old School Runescape Grand Exchange and calculates potential profits from herb farming runs and cooking fish. Unlike the OSRS Wiki herb calculator, this bot uses a different method to fetch Grand Exchange prices for items, providing more accurate current prices.

## Commands

The bot commands are configured in a way that the parameters for the command will be prompted and autofilled by the bot.

```/herb_profit```

```/fish_profit```

## Roadmap 📋✨

Feel free to submit ideas (as issues) or pull requests for requested or nice-to-have features. See the projects board for accurate feature/issue tracking.

### New User Options for Commands 🛠️

- [x] Allow users to set if they want the latest price or 1h average

### New Commands 🎣🔥

- [x] **Raw Fish vs. Cooked Fish Price Check**:
  - Fetch current Grand Exchange prices for raw fish 🐟.
  - Fetch current Grand Exchange prices for cooked fish 🍣.
  - Calculate the potential profit from cooking each type of fish 💰.
  - Display the profit data in a nicely formatted table in Discord 📊.

- [ ] **Item Price Potential**:
  - Fetch Grand Exchange price for high volume + profit margin items 💎.

## Folder Structure

```bash
osrs_utilities/
├── assets/
│   ├── images/
├── bot/ 
│   ├── __init__.py
│   ├── bot.py 
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── herb_profit.py  # Herb profit command logic
│   │   ├── fish_profit.py  # Fish profit command logic (future)
│   │   └── # Other command modules
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── api.py  # API fetching logic
│   │   ├── calculations.py  # Calculation logic
│   │   └── helpers.py  # Helper functions
├── config/
│   ├── __init__.py
│   ├── config.yaml #-contains the bot config values
│   ├── settings.py #-loads all settings from .env and config
├── data/
│   ├── __init__.py
│   ├── items.py #-sets all item IDs required
├── tests/  # Test cases for the bot
│   ├── __init__.py
│   ├── test_commands.py
│   ├── test_utils.py
│   └── # Other test modules
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── LICENSE.txt
├── README.md
├── requirements.txt
└── run.py #-main logic to run/start the bot
```

## Setup

### Prerequisites

- Python 3.7+
- Docker and Docker Compose
- A Discord account and a Discord server where you have permission to add bots.

### Installation (local)

1. **Clone the repository:**

    ```bash
    git clone https://github.com/PrettyNeet/OSRS_Utilities
    cd osrs_utilities
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables:**

    Create a ```.env``` file in the root directory and add your Discord bot token:

    ```env
    DISCORD_BOT_TOKEN=your_discord_bot_token
    ```

4. **Configure settings:**

    Update ```config.yaml``` with any additional settings you need.

    ```yaml
    bot_prefix:
    intents:
    headers:
    debug:
    ```

5. **Run the bot:**

    ```bash
    python .\run.py
    ```

## Installation (Docker)

1. **Clone the repository:**

    ```bash
    git clone https://github.com/PrettyNeet/OSRS_Utilities
    cd osrs_utilities
    ```

2. **Set up environment variables:**

    Create a .env file in the root directory and add your Discord bot token:

    ```env
    DISCORD_BOT_TOKEN=your_discord_bot_token
    ```

    Build and run the Docker container:

    ```bash
    docker-compose up --build
    ```

## Usage

- Add your bot to your Discord server using the OAuth2 URL generated in the Discord Developer Portal.
- refer to the command section or bot.py for all commands

## Debugging

To enable or disable debugging, set the debug value in config/config.yaml:

```yaml
debug: true
```

When debugging is enabled, additional information will be printed to the console to help diagnose issues.

## Adding New Commands and Features

To add new commands and features, follow these steps:

1. **Create a new command file:**

- If you have multiple commands related to a feature, you might want to group them in a separate file.
- create the new command file in /commands/ folder

2. **Define the command in the command file:**

- Implement the command as a class inheriting from commands.Cog.
- Register the command using the @commands.command() decorator.

3. **Add utility functions (if needed):**

- re-use any of the helper utilities found in the /utils/ folder
- if a new utility is identified, create one here to be re-used later in new commands

4. **Load the new command in run.py and/or bot.py:**

- Ensure the new command file is imported and the setup function is called.

## Contributing

Feel free to submit issues or pull requests if you have any improvements or features you would like to add.

## Acknowledgements

This project was heavily inspired by the [OSRS Wiki](https://oldschool.runescape.wiki/), which provides a wealth of information and tools for Old School RuneScape players. Special thanks to the contributors of the OSRS Wiki for their extensive work in maintaining and updating the resources that make projects like this possible.

The farming yield logic is heavy based on the [herb farming calculator](https://oldschool.runescape.wiki/w/Calculator:Farming/Herbs)

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
This project is licensed under the MIT License.
