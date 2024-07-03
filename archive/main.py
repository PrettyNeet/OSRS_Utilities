import os
import requests
import discord
from discord.ext import commands
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch the bot token from environment variable
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Check if the token is loaded correctly
if TOKEN is None:
    raise ValueError("DISCORD_BOT_TOKEN environment variable not set")

# Define the intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

headers = {
    'User-Agent': "Herb Run - Realtime Check",
    'From': "@mistrustful on discord and osrs"
}

#All the herbs, their seed price in a list
herbs = {
    "Guam": {"seed_id": 5291, "herb_id": 199},
    "Marrentill": {"seed_id": 5292, "herb_id": 201},
    "Tarromin": {"seed_id": 5293, "herb_id": 203},
    "Harralander": {"seed_id": 5294, "herb_id": 205},
    "Ranarr": {"seed_id": 5295, "herb_id": 207},
    "Toadflax": {"seed_id": 5296, "herb_id": 3049},
    "Irit": {"seed_id": 5297, "herb_id": 209},
    "Avantoe": {"seed_id": 5298, "herb_id": 211},
    "Kwuarm": {"seed_id": 5299, "herb_id": 213},
    "Snapdragon": {"seed_id": 5300, "herb_id": 3051},
    "Cadantine": {"seed_id": 5301, "herb_id": 215},
    "Lantadyme": {"seed_id": 5302, "herb_id": 2485},
    "Dwarf weed": {"seed_id": 5303, "herb_id": 217},
    "Torstol": {"seed_id": 5304, "herb_id": 219}
}
#To do: add ticks and math for potential yield based on lvl, patches, compost, etc.
'''compostLifeValue = {
    "None": 0,
    "Compost": 1,
    "SuperCompost": 2,
    "UltraCompost": 3
}
compostChance = {
    "None": 1,
    "Compost": 2,
    "SuperCompost": 5,
    "UltraCompost": 10
}'''

# Function to fetch latest prices from the API
'''def fetch_latest_prices(item_ids):
    url = "https://prices.runescape.wiki/api/v1/osrs/latest"
    response = requests.get(url, params={"id": ",".join(map(str, item_ids))}, headers=headers)
    data = response.json()
    #debug
    print("API Response: ", data)
    if "data" not in data:
        raise ValueError("Error fetching data from API")
    return data["data"]
''' #old fetch function 

def fetch_latest_prices():
    url = "https://prices.runescape.wiki/api/v1/osrs/latest"
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if "data" not in data:
        raise ValueError("Error fetching data from API")
    return data["data"]

#func to calculate profit
'''def calculate_potential_profit(prices, herbs, avg_yield=8, nb_patches=9):
    results = []
    for herb, info in herbs.items():
        seed_id_str = str(info["seed_id"])
        herb_id_str = str(info["herb_id"])
        
        # Check if both seed_id and herb_id are present in the prices data
        if seed_id_str not in prices or herb_id_str not in prices:
            print(f"Missing data for {herb} (seed_id: {seed_id_str}, herb_id: {herb_id_str})")
            continue
        
        seed_price = prices[seed_id_str]["high"]
        herb_price = prices[herb_id_str]["high"]
        
        profit_per_seed = (herb_price * avg_yield) - seed_price
        results.append({"Herb": herb, "Seed Price": seed_price, "Grimy Herb Price": herb_price,
                        "Profit per Seed": profit_per_seed, "Profit per run": (profit_per_seed * nb_patches)})
    return results
''' #old profits function

# Function to calculate potential profit
def calculate_potential_profit(prices, herbs, average_yield=8, farm_plots=9):
    results = []
    for herb, info in herbs.items():
        seed_id_str = str(info["seed_id"])
        herb_id_str = str(info["herb_id"])
        
        # Check if both seed_id and herb_id are present in the prices data
        if seed_id_str not in prices or herb_id_str not in prices:
            print(f"Missing data for {herb} (seed_id: {seed_id_str}, herb_id: {herb_id_str})")
            continue
        
        seed_price = prices[seed_id_str]["high"]
        herb_price = prices[herb_id_str]["high"]
        profit_per_seed = (herb_price * average_yield) - seed_price
        profit_per_run = profit_per_seed * farm_plots
        results.append({"Herb": herb, "Seed Price": seed_price, "Grimy Herb Price": herb_price,
                        "Potential Yield": average_yield, "Profit per Seed": profit_per_seed, "Profit per Run": profit_per_run})
    
    return results
'''
# Get the item IDs for the seeds and herbs
item_ids = []
for herb_info in herbs.values():
    item_ids.append(herb_info["seed_id"])
    item_ids.append(herb_info["herb_id"])

# Fetch the latest prices
try:
    latest_prices = fetch_latest_prices(item_ids)
except ValueError as e:
    print("en error ocurred:  {e}")
    latest_prices = {}

# Calculate potential profits
if latest_prices:
    profit_results = calculate_potential_profit(latest_prices, herbs)
    # Display results in a pandas DataFrame
    df = pd.DataFrame(profit_results)
    print(df)
    '''
#init bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

@bot.command()
async def herb_profit(ctx):
    try:
        latest_prices = fetch_latest_prices()
        profit_results = calculate_potential_profit(latest_prices, herbs)
        
        # Debug print the profit_results to ensure it's correct
        await ctx.send(f"Debug profit_results: {profit_results}")

        # Check the structure of profit_results
        if not profit_results:
            await ctx.send("No profit data available.")
            return

        # Check the structure of each item in profit_results
        for item in profit_results:
            if not isinstance(item, dict):
                await ctx.send(f"Unexpected item type in profit_results: {type(item)}")
                return
            for key, value in item.items():
                if not isinstance(key, str) or not isinstance(value, (int, float, str)):
                    await ctx.send(f"Unexpected key-value pair in profit_results: {key}: {value} ({type(key)}, {type(value)})")
                    return

        df = pd.DataFrame(profit_results)
        
        # Sort the DataFrame by "Profit per Run" column
        df_sorted = df.sort_values(by="Profit per Run", ascending=False)
        
        # Construct the table header
        response = "Herb Profit per Run:\n"
        response += "```"
        response += f"{'Herb':<12} {'Seed Price':<12} {'Herb Price':<12} {'Profit per Run':<15}\n"
        response += f"{'-'*12} {'-'*12} {'-'*12} {'-'*15}\n"
        
        # Add each row to the table
        for index, row in df_sorted.iterrows():
            response += f"{row['Herb']:<12} {row['Seed Price']:<12} {row['Grimy Herb Price']:<12} {row['Profit per Run']:<15.2f}\n"
        
        response += "```"
        
        await ctx.send(response)
    except ValueError as e:
        await ctx.send(f"An error occurred: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

# Run the bot with the token from environment variable
bot.run(TOKEN)

#comment out the bot lines, and un comment the below to run as local
'''
# Fetch the latest prices
try:
    latest_prices = fetch_latest_prices()
except ValueError as e:
    print(f"An error occurred: {e}")
    latest_prices = {}

# Calculate potential profits if prices were fetched successfully
if latest_prices:
    profit_results, profit_per_run = calculate_potential_profit(latest_prices, herbs)

    # Display results in a pandas DataFrame
    df = pd.DataFrame(profit_results)
    df_sorted = df.sort_values(by="Profit per Run", ascending=False)
    print(df_sorted)
    '''

