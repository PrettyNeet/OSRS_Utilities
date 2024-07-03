import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
from bot.utils import fetch_latest_prices, calculate_custom_profit
from data.items import herbs

class FormatSelectView(discord.ui.View):
    def __init__(self, bot, interaction, farming_level, patches, weiss, trollheim, hosidius, fortis, kandarin_diary, kourend, magic_secateurs, farming_cape, bottomless_bucket, compost):
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
        self.compost = compost

    @discord.ui.select(
        placeholder="Select an option...",
        options=[
            discord.SelectOption(label="Markdown Code Block", value="markdown"),
            discord.SelectOption(label="Embed with Fields", value="embed"),
        ],
        custom_id="select_format"
    )
    async def select_callback(self, interaction, select):
        format_choice = interaction.data["values"][0]
        await interaction.response.defer()

        latest_prices = fetch_latest_prices()
        profit_results = calculate_custom_profit(
            latest_prices, herbs, self.farming_level, self.patches, self.weiss,
            self.trollheim, self.hosidius, self.fortis, self.compost, self.kandarin_diary,
            self.kourend, self.magic_secateurs, self.farming_cape, self.bottomless_bucket
        )

        if not profit_results:
            await self.interaction.followup.send("No profit data available.")
            return

        df = pd.DataFrame(profit_results)
        df_sorted = df.sort_values(by="Profit per Run", ascending=False)

        if format_choice == "markdown":
            table_header = f"{'Herb':<12} {'Seed Price':<12} {'Herb Price':<12} {'Profit per Run':<15}\n{'-'*12} {'-'*12} {'-'*12} {'-'*15}\n"
            table_rows = ""
            for index, row in df_sorted.iterrows():
                table_rows += f"{row['Herb']:<12} {row['Seed Price']:<12} {row['Grimy Herb Price']:<12} {int(row['Profit per Run']):<15}\n"
            table = f"```{table_header}{table_rows}```"
            await self.interaction.followup.send(table)
        elif format_choice == "embed":
            embed = discord.Embed(title="Herb Profit per Run", color=discord.Color.green())
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
            await self.interaction.followup.send(embed=embed)

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
        view = FormatSelectView(
            bot=self.bot, interaction=interaction, farming_level=farming_level, patches=patches, 
            weiss=weiss, trollheim=trollheim, hosidius=hosidius, fortis=fortis, kandarin_diary=kandarin_diary, 
            kourend=kourend, magic_secateurs=magic_secateurs, farming_cape=farming_cape, bottomless_bucket=bottomless_bucket, 
            compost=compost.value
        )
        await interaction.response.send_message("Choose the format for the reply:", view=view)

async def setup(bot):
    await bot.add_cog(HerbProfit(bot))
