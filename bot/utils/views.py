from discord.ui import View, Button
from discord import ButtonStyle

class ProfitView(View):
    def __init__(self, calculation_callback):
        super().__init__(timeout=180)  # 3 minute timeout
        self.calculation_callback = calculation_callback
        
        # Add refresh button
        refresh_button = Button(
            style=ButtonStyle.green,
            label="🔄 Refresh Prices",
            custom_id="refresh_prices"
        )
        self.add_item(refresh_button)
    
    async def refresh_prices_callback(self, interaction):
        """Refresh prices and update the message"""
        await interaction.response.defer()
        new_data = await self.calculation_callback()
        new_embed = create_profit_embed("Updated Profit Calculation", new_data)
        await interaction.message.edit(embed=new_embed, view=self)