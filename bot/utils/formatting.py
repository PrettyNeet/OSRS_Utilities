from discord import Embed, Color
import datetime

def create_profit_embed(title: str, data: dict, description: str = None) -> Embed:
    """Creates a standardized embed for profit calculations"""
    embed = Embed(
        title=title,
        description=description,
        color=Color.green() if data.get('profit', 0) > 0 else Color.red()
    )
    
    # Add fields with inline formatting
    for key, value in data.items():
        # Format numbers with commas and round floats
        if isinstance(value, (int, float)):
            value = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}"
        embed.add_field(
            name=key.replace('_', ' ').title(),
            value=value,
            inline=True
        )
    
    # Add footer with timestamp
    embed.set_footer(text="Prices updated")
    embed.timestamp = datetime.datetime.utcnow()
    
    return embed