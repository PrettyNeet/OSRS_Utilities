import discord
from discord.ext import commands
from discord import app_commands
from bot.utils.api import fetch_latest_prices, fetch_1h_prices
from data.items import fish
import pandas as pd


class FormatSelectView(discord.ui.View):
    def __init__(self, bot, interaction, fish_prices):
        super().__init__()
        self.bot = bot
        self.interaction = interaction
        self.fish_prices = fish_prices

    @discord.ui.select(
        placeholder="Select an option...",
        options=[
            discord.SelectOption(label="Markdown Code Block", value="markdown"),
            discord.SelectOption(label="Embed with Fields", value="embed"),
        ],
        custom_id="select_format"
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Ensure only the original user can interact with this view
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("This menu is not for you.", ephemeral=True)
            return

        format_choice = select.values[0]
        await interaction.response.defer()

        if not self.fish_prices:
            await self.interaction.followup.send("No profit data available.")
            return

        df = pd.DataFrame(self.fish_prices)
        df_sorted = df.sort_values(by="GP/hr", ascending=False)

        if format_choice == "markdown":
            table_header = f"{'Fish':<12} {'Raw Price':<12} {'Cooked Price':<12} {'Profit':<12} {'XP/hr':<12} {'GP/hr':<12}\n{'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*12}\n"
            table_rows = ""
            for index, row in df_sorted.iterrows():
                table_rows += f"{row['Fish']:<12} {row['Raw Price']:<12} {row['Cooked Price']:<12} {int(row['Profit']):<12} {row['XP/hr']:<12} {row['GP/hr']:<12}\n"
            table = f"```{table_header}{table_rows}```"
            await self.interaction.followup.send(content=f"{self.interaction.user.mention} Here are the results:\n{table}")

        elif format_choice == "embed":
            embed = discord.Embed(title="Fish Cooking Profit", color=discord.Color.blue())
            embed.set_author(name=self.interaction.user.display_name, icon_url=self.interaction.user.display_avatar.url)
            for index, row in df_sorted.iterrows():
                embed.add_field(
                    name=row['Fish'],
                    value=(
                        f"**Raw Price:** {row['Raw Price']}\n"
                        f"**Cooked Price:** {row['Cooked Price']}\n"
                        f"**Profit:** {int(row['Profit'])}\n"
                        f"**XP/hr:** {row['XP/hr']}\n"
                        f"**GP/hr:** {row['GP/hr']}\n"
                    ),
                    inline=False
                )
            await self.interaction.followup.send(content=f"{self.interaction.user.mention} Here are the results:", embed=embed)


class FishProfit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fish_profit", description="Calculate the potential profit from cooking fish.")
    @app_commands.choices(
        price_type=[
            app_commands.Choice(name="Latest", value="latest"),
            app_commands.Choice(name="1-hour average", value="1h"),
        ]
    )
    async def fish_profit(self, interaction: discord.Interaction, price_type: app_commands.Choice[str]):
        session = getattr(self.bot, 'http_session', None)
        if price_type.value == "latest":
            prices = await fetch_latest_prices(session=session)
            price_key = "high"
        elif price_type.value == "1h":
            prices = await fetch_1h_prices(session=session)
            price_key = "avgHighPrice"
        else:
            await self.interaction.followup.send("error in price type selection")
            return
            
        cooking_rate = 1435

        profit_results = []
        for fish_name, info in fish.items():
            raw_id_str = str(info["raw_id"])
            cooked_id_str = str(info["cooked_id"])
            fish_xp_each = info["xp_each"]
            raw_price = prices[raw_id_str][price_key]
            cooked_price = prices[cooked_id_str][price_key]

            if raw_price and cooked_price:
                profit_fish = cooked_price - raw_price
                xphr = cooking_rate * fish_xp_each
                gphr = cooking_rate * profit_fish
                profit_results.append({
                    "Fish": fish_name,
                    "Raw Price": raw_price,
                    "Cooked Price": cooked_price,
                    "Profit": profit_fish,
                    "XP/hr": xphr,
                    "GP/hr": gphr
                })

        view = FormatSelectView(bot=self.bot, interaction=interaction, fish_prices=profit_results)
        await _send_format_prompt(interaction, view)


async def _send_format_prompt(interaction, view):
    """Send the format selection prompt from within an async handler."""
    await interaction.response.send_message(
        "Choose the format for the reply:",
        view=view,
        ephemeral=True
    )


async def setup(bot):
    await bot.add_cog(FishProfit(bot))
