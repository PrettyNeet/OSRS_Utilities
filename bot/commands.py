import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
from bot.utils import fetch_latest_prices, calculate_custom_profit
from data.items import herbs

class HerbProfit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="herb_profit", description="Calculate the potential profit from herb farming runs.")
    @app_commands.describe(
        farming_level="Your farming level",
        patches="Number of herb patches",
        weiss="Use disease-free Weiss patch",
        trollheim="Use disease-free Trollheim patch",
        hosidius="Use disease-free Hosidius patch",
        fortis="Use disease-free Civitas illa Fortis patch",
        kandarin_diary="Kandarin diary level (None/5%/10%/15%)",
        kourend="Completed Kourend hard diary",
        magic_secateurs="Use Magic Secateurs",
        farming_cape="Have Farming cape equipped",
        bottomless_bucket="Use Bottomless compost bucket"
    )
    async def herb_profit(
        self, 
        interaction: discord.Interaction, 
        farming_level: int, 
        patches: int, 
        weiss: bool, 
        trollheim: bool, 
        hosidius: bool, 
        fortis: bool, 
        kandarin_diary: str, 
        kourend: bool, 
        magic_secateurs: bool, 
        farming_cape: bool, 
        bottomless_bucket: bool, 
        compost: str
    ):
        try:
            latest_prices = fetch_latest_prices()
            profit_results = calculate_custom_profit(latest_prices, herbs, farming_level, patches, weiss, trollheim, hosidius, fortis, compost, kandarin_diary, kourend, magic_secateurs, farming_cape, bottomless_bucket)

            if not profit_results:
                await interaction.response.send_message("No profit data available.")
                return

            df = pd.DataFrame(profit_results)
            df_sorted = df.sort_values(by="Profit per Run", ascending=False)

            embed = discord.Embed(title="Herb Profit per Run", color=discord.Color.green())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

            # Create the table header
            table_header = f"{'Herb':<12} {'Seed Price':<12} {'Herb Price':<12} {'Profit per Run':<15}\n"
            table_header += f"{'-'*12} {'-'*12} {'-'*12} {'-'*15}\n"

            # Create the table rows
            table_rows = ""
            for index, row in df_sorted.iterrows():
                table_rows += f"{row['Herb']:<12} {row['Seed Price']:<12} {row['Grimy Herb Price']:<12} {int(row['Profit per Run']):<15}\n"

            # Combine header and rows
            table = f"```{table_header}{table_rows}```"

            # Add the table to the embed
            embed.description = table

            await interaction.response.send_message(embed=embed)
        except ValueError as e:
            await interaction.response.send_message(f"An error occurred: {e}")
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(HerbProfit(bot))

class HerbProfit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="herb_profit", description="Calculate the potential profit from herb farming runs.")
    @app_commands.describe(
        farming_level="Your farming level",
        patches="Number of herb patches",
        weiss="Use disease-free Weiss patch",
        trollheim="Use disease-free Trollheim patch",
        hosidius="Use disease-free Hosidius patch",
        fortis="Use disease-free Civitas illa Fortis patch",
        kandarin_diary="Kandarin diary level (None/5%/10%/15%)",
        kourend="Completed Kourend hard diary",
        magic_secateurs="Use Magic Secateurs",
        farming_cape="Have Farming cape equipped",
        bottomless_bucket="Use Bottomless compost bucket"
    )
    @app_commands.choices(
        compost=[
            app_commands.Choice(name="None", value="None"),
            app_commands.Choice(name="Compost", value="Compost"),
            app_commands.Choice(name="Supercompost", value="Supercompost"),
            app_commands.Choice(name="Ultracompost", value="Ultracompost"),
        ]
    )
#TODO fix the embed output of the message to better display information
    async def herb_profit(
        self, 
        interaction: discord.Interaction, 
        farming_level: int, 
        patches: int, 
        weiss: bool, 
        trollheim: bool, 
        hosidius: bool, 
        fortis: bool, 
        kandarin_diary: str, 
        kourend: bool, 
        magic_secateurs: bool, 
        farming_cape: bool, 
        bottomless_bucket: bool, 
        compost: app_commands.Choice[str]
    ):
        try:
            latest_prices = fetch_latest_prices()
            profit_results = calculate_custom_profit(latest_prices, herbs, farming_level, patches, weiss, trollheim, hosidius, fortis, compost.value, kandarin_diary, kourend, magic_secateurs, farming_cape, bottomless_bucket)

            if not profit_results:
                await interaction.response.send_message("No profit data available.")
                return

            df = pd.DataFrame(profit_results)
            df_sorted = df.sort_values(by="Profit per Run", ascending=False)

            embed = discord.Embed(title="Herb Profit per Run", color=discord.Color.green())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

            # Create the table header
            table_header = f"{'Herb':<12} {'Seed Price':<12} {'Herb Price':<12} {'Profit per Run':<15}\n"
            table_header += f"{'-'*12} {'-'*12} {'-'*12} {'-'*15}\n"

            # Create the table rows
            table_rows = ""
            for index, row in df_sorted.iterrows():
                table_rows += f"{row['Herb']:<12} {row['Seed Price']:<12} {row['Grimy Herb Price']:<12} {int(row['Profit per Run']):<15}\n"

            # Combine header and rows
            table = f"```{table_header}{table_rows}```"

            # Add the table to the embed
            embed.description = table

            await interaction.response.send_message(embed=embed)
        except ValueError as e:
            await interaction.response.send_message(f"An error occurred: {e}")
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(HerbProfit(bot))
