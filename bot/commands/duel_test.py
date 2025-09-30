from discord import app_commands, Interaction, Member
from discord.ext import commands
from discord.ui import View, Button, Select
from typing import Dict, Optional, List
from datetime import datetime
import discord
from bot.utils.combat_mechanics_test import (
    calculate_hit_chance, calculate_damage,
    calculate_special_attack, calculate_combat_stats,
    apply_prayer_bonuses
)
from bot.utils.combat_views_test import DuelRequestView, CombatActionView, EquipmentView
from bot.utils.DButil_v2 import (
    get_user_stats, get_user_equipment,
    get_user_inventory, update_user_stats,
    update_duel_history
)

class DuelState:
    """State management for an active duel"""
    def __init__(
        self,
        challenger: Member,
        opponent: Member,
        challenger_stats: Dict,
        opponent_stats: Dict,
        challenger_equipment: Dict,
        opponent_equipment: Dict,
        start_time: datetime
    ):
        self.challenger = challenger
        self.opponent = opponent
        self.challenger_stats = challenger_stats
        self.opponent_stats = opponent_stats
        self.challenger_equipment = challenger_equipment
        self.opponent_equipment = opponent_equipment
        self.start_time = start_time
        
        self.current_turn = challenger
        self.winner = None
        self.special_attack_cooldown = {}
    
    def get_opponent(self, user: Member) -> Member:
        """Get opponent of given user"""
        return self.opponent if user.id == self.challenger.id else self.challenger
    
    def get_health(self, user: Member) -> int:
        """Get current health of user"""
        stats = self.challenger_stats if user.id == self.challenger.id else self.opponent_stats
        return stats["current_health"]
    
    def get_equipment(self, user: Member) -> Dict:
        """Get equipment of user"""
        return self.challenger_equipment if user.id == self.challenger.id else self.opponent_equipment
    
    def get_stats(self, user: Member) -> Dict:
        """Get stats of user"""
        return self.challenger_stats if user.id == self.challenger.id else self.opponent_stats
    
    def create_status_embed(self) -> discord.Embed:
        """Create status embed for current duel state"""
        embed = discord.Embed(title="Duel Status", color=0x00ff00)
        
        # Add challenger info
        challenger_health = self.get_health(self.challenger)
        challenger_weapon = self.challenger_equipment.get("weapon", {}).get("name", "Unarmed")
        embed.add_field(
            name=f"{self.challenger.display_name}",
            value=f"Health: {challenger_health}\nWeapon: {challenger_weapon}",
            inline=True
        )
        
        # Add opponent info
        opponent_health = self.get_health(self.opponent)
        opponent_weapon = self.opponent_equipment.get("weapon", {}).get("name", "Unarmed")
        embed.add_field(
            name=f"{self.opponent.display_name}",
            value=f"Health: {opponent_health}\nWeapon: {opponent_weapon}",
            inline=True
        )
        
        # Add current turn indicator
        embed.add_field(
            name="Current Turn",
            value=f"{self.current_turn.display_name}'s turn!",
            inline=False
        )
        
        return embed

class DuelCommand(commands.Cog):
    """Duel command implementation"""
    def __init__(self, bot):
        self.bot = bot
        self.active_duels: Dict[int, DuelState] = {}
        self.DUEL_TIMEOUT = 300  # 5 minutes
    
    @app_commands.command(name="duel")
    async def duel(self, interaction: Interaction, opponent: Member):
        """Challenge another user to a duel"""
        
        # Validate users
        if opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "You can't duel yourself!",
                ephemeral=True
            )
            return
            
        if opponent.bot:
            await interaction.response.send_message(
                "You can't duel a bot!",
                ephemeral=True
            )
            return
        
        # Check if either user is in an active duel
        if interaction.user.id in self.active_duels:
            await interaction.response.send_message(
                "You're already in a duel!",
                ephemeral=True
            )
            return
            
        if opponent.id in self.active_duels:
            await interaction.response.send_message(
                f"{opponent.display_name} is already in a duel!",
                ephemeral=True
            )
            return
        
        # Create duel request view
        view = DuelRequestView(
            challenger=interaction.user,
            opponent=opponent,
            timeout=60
        )
        
        # Send duel request
        await interaction.response.send_message(
            f"{interaction.user.mention} has challenged {opponent.mention} to a duel!",
            view=view
        )
        
        # Wait for response
        await view.wait()
        
        if view.accepted:
            # Initialize duel state
            duel_state = await self._initialize_duel(interaction.user, opponent)
            self.active_duels[interaction.user.id] = duel_state
            self.active_duels[opponent.id] = duel_state
            
            # Start combat
            await self._start_combat(interaction, duel_state)
        
        elif view.declined:
            await interaction.followup.send(
                f"{opponent.display_name} declined the duel!"
            )
        
        else:
            await interaction.followup.send(
                "The duel request timed out."
            )
    
    async def _initialize_duel(
        self,
        challenger: Member,
        opponent: Member
    ) -> DuelState:
        """Initialize duel state with user stats and equipment"""
        challenger_stats = await get_user_stats(challenger.id)
        opponent_stats = await get_user_stats(opponent.id)
        
        challenger_equipment = await get_user_equipment(challenger.id)
        opponent_equipment = await get_user_equipment(opponent.id)
        
        return DuelState(
            challenger=challenger,
            opponent=opponent,
            challenger_stats=challenger_stats,
            opponent_stats=opponent_stats,
            challenger_equipment=challenger_equipment,
            opponent_equipment=opponent_equipment,
            start_time=datetime.now()
        )
    
    async def _start_combat(
        self,
        interaction: Interaction,
        duel_state: DuelState
    ):
        """Start combat phase of duel"""
        embed = duel_state.create_status_embed()
        view = CombatActionView(
            attacker=duel_state.current_turn,
            defender=duel_state.get_opponent(duel_state.current_turn),
            duel_state=duel_state
        )
        
        await interaction.followup.send(
            "Battle begins!",
            embed=embed,
            view=view
        )
    
    async def _handle_duel_completion(self, user_id: int):
        """Handle duel completion and cleanup"""
        if user_id in self.active_duels:
            duel_state = self.active_duels[user_id]
            
            # Update user stats
            await update_user_stats(
                duel_state.winner.id,
                {"total_wins": "+1"}
            )
            await update_user_stats(
                duel_state.get_opponent(duel_state.winner).id,
                {"total_losses": "+1"}
            )
            
            # Record duel history
            await update_duel_history(
                winner_id=duel_state.winner.id,
                loser_id=duel_state.get_opponent(duel_state.winner).id,
                duration=(datetime.now() - duel_state.start_time).seconds,
                winner_hp=duel_state.get_health(duel_state.winner),
                loser_hp=0
            )
            
            # Cleanup
            challenger_id = duel_state.challenger.id
            opponent_id = duel_state.opponent.id
            self.active_duels.pop(challenger_id, None)
            self.active_duels.pop(opponent_id, None)

async def setup(bot: commands.Bot):
    await bot.add_cog(DuelCommand(bot))