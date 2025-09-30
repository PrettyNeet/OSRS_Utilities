from difrom bot.utils.combat_mechanics import (
    calculate_max_hit, calculate_accuracy,
    calculate_defense, calculate_hit_chance,
    calculate_special_attack, calculate_damage)d import Interaction, Member
from discord.ui import View, Button, Select
from typing import Optional, Dict, List
import asyncio
import discord
from datetime import datetime
import random
from bot.utils.combat_mechanics_test import (
    calculate_hit_chance, calculate_damage,
    calculate_special_attack, calculate_combat_stats,
    apply_prayer_bonuses
)

class DuelRequestView(View):
    def __init__(
        self,
        challenger: Member,
        opponent: Member,
        timeout: float = 60.0
    ):
        super().__init__(timeout=timeout)
        self.challenger = challenger
        self.opponent = opponent
        self.accepted = False
        self.declined = False
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        """Only allow the opponent to interact with this view"""
        return interaction.user.id == self.opponent.id
    
    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id="accept"
    )
    async def accept_button(
        self,
        interaction: Interaction,
        button: Button
    ):
        self.accepted = True
        self.stop()
        await interaction.response.edit_message(
            content=f"{self.opponent.display_name} accepted the duel!",
            view=None
        )
    
    @discord.ui.button(
        label="Decline",
        style=discord.ButtonStyle.red,
        custom_id="decline"
    )
    async def decline_button(
        self,
        interaction: Interaction,
        button: Button
    ):
        self.declined = True
        self.stop()
        await interaction.response.edit_message(
            content=f"{self.opponent.display_name} declined the duel.",
            view=None
        )

class CombatActionView(View):
    def __init__(
        self,
        attacker: Member,
        defender: Member,
        duel_state: 'DuelState',
        timeout: float = 60.0
    ):
        super().__init__(timeout=timeout)
        self.attacker = attacker
        self.defender = defender
        self.duel_state = duel_state
        self.action_selected = False
        self.selected_action = None
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        """Only allow the current attacker to interact with this view"""
        return interaction.user.id == self.attacker.id
    
    @discord.ui.button(
        label="Attack",
        style=discord.ButtonStyle.primary,
        custom_id="attack"
    )
    async def attack_button(
        self,
        interaction: Interaction,
        button: Button
    ):
        self.action_selected = True
        self.selected_action = "attack"
        self.stop()
        
        # Calculate hit
        attacker_stats = self.duel_state.get_stats(self.attacker)
        defender_stats = self.duel_state.get_stats(self.defender)
        weapon = self.duel_state.get_equipment(self.attacker).get("weapon")
        
        attack_roll = calculate_accuracy(
            attack_level=attacker_stats["attack"],
            attack_bonus=weapon.get("attack_bonus", 0)
        )
        
        defense_roll = calculate_defense(
            defense_level=defender_stats["defense"],
            defense_bonus=0  # TODO: Add armor bonuses
        )
        
        if calculate_hit_chance(attack_roll, defense_roll) > random.random():
            damage = calculate_damage(
                strength_level=attacker_stats["strength"],
                strength_bonus=weapon.get("strength_bonus", 0),
                weapon_damage=weapon.get("damage", 1)
            )
            
            # Update health
            defender_stats["current_health"] -= damage
            await interaction.response.edit_message(
                content=f"{self.attacker.display_name} hits {self.defender.display_name} for {damage} damage!",
                embed=self.duel_state.create_status_embed(),
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f"{self.attacker.display_name}'s attack missed!",
                embed=self.duel_state.create_status_embed(),
                view=None
            )
    
    @discord.ui.button(
        label="Special Attack",
        style=discord.ButtonStyle.danger,
        custom_id="special"
    )
    async def special_button(
        self,
        interaction: Interaction,
        button: Button
    ):
        weapon = self.duel_state.get_equipment(self.attacker).get("weapon")
        
        if not weapon or not weapon.get("special_attack"):
            await interaction.response.send_message(
                "You don't have a weapon with a special attack!",
                ephemeral=True
            )
            return
        
        if self.attacker.id in self.duel_state.special_attack_cooldown:
            cooldown = self.duel_state.special_attack_cooldown[self.attacker.id]
            if (datetime.now() - cooldown).seconds < 30:
                await interaction.response.send_message(
                    "Special attack is on cooldown!",
                    ephemeral=True
                )
                return
        
        self.action_selected = True
        self.selected_action = "special"
        self.stop()
        
        # Process special attack
        attacker_stats = self.duel_state.get_stats(self.attacker)
        base_damage = calculate_damage(
            strength_level=attacker_stats["strength"],
            strength_bonus=weapon.get("strength_bonus", 0),
            weapon_damage=weapon.get("damage", 1)
        )
        
        special_damage = calculate_special_attack(
            weapon_name=weapon["name"],
            base_damage=base_damage,
            special_cost=weapon.get("special_attack_cost", 25)
        )
        
        # Update health
        defender_stats = self.duel_state.get_stats(self.defender)
        defender_stats["current_health"] -= special_damage
        
        # Update cooldown
        self.duel_state.special_attack_cooldown[self.attacker.id] = datetime.now()
        
        await interaction.response.edit_message(
            content=f"{self.attacker.display_name} used {weapon['name']}'s special attack!\nDealt {special_damage} damage!",
            embed=self.duel_state.create_status_embed(),
            view=None
        )

class EquipmentView(View):
    def __init__(
        self,
        user: Member,
        db: Optional[Dict] = None,
        timeout: float = 180.0
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.db = db
    
    @discord.ui.select(
        placeholder="Select Weapon",
        custom_id="weapon",
        min_values=1,
        max_values=1
    )
    async def weapon_select(
        self,
        interaction: Interaction,
        select: Select
    ):
        try:
            weapon_id = int(select.values[0])
            await self.db.execute(
                """UPDATE user_equipment 
                SET weapon_id = ?
                WHERE user_id = ?""",
                (weapon_id, self.user.id)
            )
            await self.db.commit()
            
            weapon_name = next(
                opt.label for opt in select.options 
                if opt.value == select.values[0]
            )
            
            await interaction.response.send_message(
                f"Equipped {weapon_name}!",
                ephemeral=True
            )
        
        except Exception as e:
            await interaction.response.send_message(
                "An error occurred while updating equipment.",
                ephemeral=True
            )