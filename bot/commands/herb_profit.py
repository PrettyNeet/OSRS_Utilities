import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
from bot.utils.api import fetch_latest_prices, fetch_1h_prices
from bot.utils.calculations import calculate_custom_profit
from bot.utils.logger import setup_logging
from data.items import herbs

# setting the logger
logger = setup_logging()


# Setting the VIEW class to handle user format selection, interactive within discord channel message
class FormatSelectView(discord.ui.View):
    def __init__(self, bot, interaction, farming_level, patches, weiss, trollheim, hosidius, fortis, kandarin_diary, kourend, magic_secateurs, farming_cape, bottomless_bucket, attas, compost, prices, price_key, price_type):
        super().__init__()
        self.bot = bot
        self.interaction = interaction
        self.farming_level = farming_level
        self.patches = patches
        self.weiss = weiss
        self.trollheim = trollheim
        self.hosidius = hosidius
        self.fortis = fortis
        self.kandarin_diary = kandarin_diary
        self.kourend = kourend
        self.magic_secateurs = magic_secateurs
        self.farming_cape = farming_cape
        self.bottomless_bucket = bottomless_bucket
        self.attas = attas
        self.compost = compost
        self.prices = prices
        self.price_key = price_key
        self.price_type = price_type

    # Select menu for format, set's the option for the bot to later format the reply
    @discord.ui.select(
        placeholder="Select an option...",
        options=[
            discord.SelectOption(label="Markdown Code Block", value="markdown"),
            discord.SelectOption(label="Embed with Fields", value="embed"),
        ],
        custom_id="select_format"
    )
    async def select_callback(self, interaction: discord.Interaction, select):
        # Ensure only the original user can interact with this view
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This menu is not for you.", ephemeral=True)
            return

        # Sets the format choice
        format_choice = interaction.data["values"][0]
        await interaction.response.defer()
        
        # Debugging: Print the prices and price_key
        logger.debug("Prices fetched: %s", self.prices)
        logger.debug("Price key:", self.price_key)

        # calculate profits
        profit_results = calculate_custom_profit(
            self.prices, herbs, self.farming_level, self.patches, self.weiss,
            self.trollheim, self.hosidius, self.fortis, self.compost, self.kandarin_diary,
            self.kourend, self.magic_secateurs, self.farming_cape, self.bottomless_bucket, self.attas, self.price_key
        )

        # Error handling if API or calc is empty
        if not profit_results:
            await self.interaction.followup.send("No profit data available.")
            logger.error("No profit data available.")
            return

        # Converting results to data frame
        df = pd.DataFrame(profit_results)
        df_sorted = df.sort_values(by="Profit per Run", ascending=False)

        # Format and send response based on user choice
        title = f"results using {self.price_type} prices"
        if format_choice == "markdown":
            table_header = f"{'Herb':<12} {'Seed Price':<12} {'Herb Price':<12} {'Profit per Run':<15}\n{'-'*12} {'-'*12} {'-'*12} {'-'*15}\n"
            table_rows = ""
            for index, row in df_sorted.iterrows():
                table_rows += f"{row['Herb']:<12} {row['Seed Price']:<12} {row['Grimy Herb Price']:<12} {int(row['Profit per Run']):<15}\n"
            table = f"```{title}\n{table_header}{table_rows}```"
            await self.interaction.followup.send(content=f"{self.interaction.user.mention} Here are the results:\n{table}")
            logger.info("success sending: %s", format_choice)

        elif format_choice == "embed":
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.set_author(name=self.interaction.user.display_name, icon_url=self.interaction.user.display_avatar.url)
            for index, row in df_sorted.iterrows():
                embed.add_field(
                    name=row['Herb'],
                    value=(
                        f"**Seed Price:** {row['Seed Price']}\n"
                        f"**Herb Price:** {row['Grimy Herb Price']}\n"
                        f"**Profit per Run:** {int(row['Profit per Run'])}\n"
                    ),
                    inline=False
                )
            await self.interaction.followup.send(content=f"{self.interaction.user.mention} Here are the results:", embed=embed)
            logger.info("success sending: %s", format_choice)


class HerbProfit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="herb_profit", description="Calculate the potential profit from herb farming runs.")
    @app_commands.describe(
        farming_level="Your farming level",
        patches="Number of total herb patches",
        weiss="Using disease-free Weiss patch",
        trollheim="Use disease-free Trollheim patch",
        hosidius="Use disease-free Hosidius patch",
        fortis="Use disease-free Civitas illa Fortis patch (champion)",
        kandarin_diary="Kandarin diary level (None/5%/10%/15%)",
        kourend="Completed Kourend hard diary",
        magic_secateurs="Use Magic Secateurs",
        farming_cape="Have Farming cape equipped",
        bottomless_bucket="Use Bottomless compost bucket",
        attas="Is attas planted in anima patch?"

    )
    @app_commands.choices(
        compost=[
            app_commands.Choice(name="None", value="None"),
            app_commands.Choice(name="Compost", value="Compost"),
            app_commands.Choice(name="Supercompost", value="Supercompost"),
            app_commands.Choice(name="Ultracompost", value="Ultracompost"),
        ],
        price_type=[
            app_commands.Choice(name="Latest", value="latest"),
            app_commands.Choice(name="1-hour average", value="1h"),
        ]
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
        attas: bool,
        compost: app_commands.Choice[str],
        price_type: app_commands.Choice[str]
    ):
        session = getattr(self.bot, 'http_session', None)
        if price_type.value == "latest":
            prices = await fetch_latest_prices(session=session)
            price_key = "high"
        elif price_type.value == "1h":
            prices = await fetch_1h_prices(session=session)
            price_key = "avgHighPrice"
        else:
            await self.interaction.followup.send("error is checking price type value")
            return
        
        # Debugging: Print the prices and price_key
        logger.debug("Prices fetched: %s", prices)
        logger.debug("Price key: %s", price_key)
        
        # Create and send a view select
        view = FormatSelectView(
            bot=self.bot, interaction=interaction, farming_level=farming_level, patches=patches,
            weiss=weiss, trollheim=trollheim, hosidius=hosidius, fortis=fortis, kandarin_diary=kandarin_diary,
            kourend=kourend, magic_secateurs=magic_secateurs, farming_cape=farming_cape, bottomless_bucket=bottomless_bucket, attas=attas,
            compost=compost.value, prices=prices, price_key=price_key, price_type=price_type.value
        )
        await interaction.response.send_message("Choose the format for the reply:", view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HerbProfit(bot))
