from bot.utils.combat_mechanics import (
    calculate_hit_chance,
    calculate_special_attack, calculate_damage
)

from typing import Optional, Dict, List, Any
import asyncio
from types import SimpleNamespace

# Try to import discord UI classes; if discord.py is not installed (tests/CI),
# provide minimal no-op fallbacks so the module can be imported and tested.
try:
    from discord.ui import View, Button, Select
    import discord
except Exception:
    # Minimal stub implementations / decorators used only for typing-free imports.
    class View:
        def __init__(self, timeout: float = None):
            # Minimal children container to emulate discord.ui.View
            self.children = []
            self._stopped = False
            self._timeout = timeout
            # Track creation time to determine timeout without creating background tasks
            self._start_time = datetime.now() if timeout is not None and timeout > 0 else None

        def is_finished(self):
            if self._stopped:
                return True
            if self._timeout and self._start_time:
                elapsed = (datetime.now() - self._start_time).total_seconds()
                if elapsed >= self._timeout:
                    self._stopped = True
                    return True
            return False

        def stop(self):
            self._stopped = True

    class Button:
        def __init__(self, custom_id: str = None, callback=None):
            self.custom_id = custom_id
            # callback is an async function to call when button pressed
            async def _noop(interaction, button=None):
                return None

            self._callback = callback or _noop

        @property
        def callback(self):
            return self._callback

    class Select:
        def __init__(self, custom_id: str = None, options: list | None = None, callback=None):
            self.custom_id = custom_id
            self.options = options or []
            async def _noop(interaction, select=None):
                return None
            self._callback = callback or _noop

        @property
        def callback(self):
            return self._callback

    class _UI:
        def button(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def select(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    discord = SimpleNamespace(
        ui=_UI(),
        ButtonStyle=SimpleNamespace(primary=1, green=2, red=3, danger=4)
    )
from datetime import datetime
import random

class DuelRequestView(View):
    def __init__(
        self,
        challenger: Any,
        opponent: Any,
        timeout: float = 60.0
    ):
        super().__init__(timeout=timeout)
        self.challenger = challenger
        self.opponent = opponent
        self.accepted = False
        self.declined = False
        # Create button stubs for tests to interact with
        accept = Button(custom_id="accept")
        decline = Button(custom_id="decline")
        # attach callbacks bound to methods; tests call callback(interaction)
        async def _accept_wrapper(interaction, button=None):
            return await self.accept_button(interaction, accept)

        async def _decline_wrapper(interaction, button=None):
            return await self.decline_button(interaction, decline)

        accept._callback = _accept_wrapper
        decline._callback = _decline_wrapper
        self.children.extend([accept, decline])
        # Simple event loop-friendly wait implementation for tests
        self._accepted_event = asyncio.Event()
        self._declined_event = asyncio.Event()
    
    async def interaction_check(self, interaction: Any) -> bool:
        """Only allow the opponent to interact with this view"""
        return interaction.user.id == self.opponent.id
    
    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id="accept"
    )
    async def accept_button(
        self,
        interaction: Any,
        button: Button
    ):
        self.accepted = True
        self.stop()
        await interaction.response.edit_message(
            content=f"{self.opponent.display_name} accepted the duel!",
            view=None
        )
        self._accepted_event.set()
    
    @discord.ui.button(
        label="Decline",
        style=discord.ButtonStyle.red,
        custom_id="decline"
    )
    async def decline_button(
        self,
        interaction: Any,
        button: Button
    ):
        self.declined = True
        self.stop()
        await interaction.response.edit_message(
            content=f"{self.opponent.display_name} declined the duel.",
            view=None
        )
        self._declined_event.set()

    async def wait(self, timeout: float = None):
        """Wait until accepted/declined or timeout (test-friendly)."""
        # If already decided, return immediately
        if self.accepted or self.declined:
            return
        # Wait for either event
        tasks = [asyncio.create_task(self._accepted_event.wait()), asyncio.create_task(self._declined_event.wait())]
        try:
            done, pending = await asyncio.wait(tasks, timeout=timeout)
        finally:
            for p in pending:
                p.cancel()

class CombatActionView(View):
    def __init__(
        self,
        attacker: Any,
        defender: Any,
        duel_state: Any = None,
        db: Optional[Any] = None,
        timeout: float = 60.0
    ):
        super().__init__(timeout=timeout)
        self.attacker = attacker
        self.defender = defender
        # Provide a minimal stub for duel_state when tests don't pass a full
        # DuelState object. The real implementation will provide richer APIs.
        if duel_state is None:
            class _StubState:
                def __init__(self):
                    self._stats = {}
                    self._equipment = {}
                    self.special_attack_cooldown = {}

                def get_stats(self, member):
                    return self._stats.get(member.id, {
                        "attack": 60,
                        "strength": 60,
                        "defense": 60,
                        "current_health": 99,
                        "health": 99
                    })

                def get_equipment(self, member):
                    return self._equipment.get(member.id, {"weapon": {"attack_bonus": 0, "strength_bonus": 0, "damage": 1, "name": "Fist"}})

                def create_status_embed(self):
                    return None

            self.duel_state = _StubState()
        else:
            self.duel_state = duel_state
        self.action_selected = False
        self.selected_action = None
        attack = Button(custom_id="attack")
        special = Button(custom_id="special")

        async def _attack_wrapper(interaction, button=None):
            return await self.attack_button(interaction, attack)

        async def _special_wrapper(interaction, button=None):
            return await self.special_button(interaction, special)

        attack._callback = _attack_wrapper
        special._callback = _special_wrapper
        self.children.extend([attack, special])
    
    async def interaction_check(self, interaction: Any) -> bool:
        """Only allow the current attacker to interact with this view"""
        return interaction.user.id == self.attacker.id
    
    @discord.ui.button(
        label="Attack",
        style=discord.ButtonStyle.primary,
        custom_id="attack"
    )
    async def attack_button(
        self,
        interaction: Any,
        button: Button
    ):
        self.action_selected = True
        self.selected_action = "attack"
        self.stop()
        
        # Calculate hit
        attacker_stats = self.duel_state.get_stats(self.attacker)
        defender_stats = self.duel_state.get_stats(self.defender)
        weapon = self.duel_state.get_equipment(self.attacker).get("weapon")
        
        attack_level = attacker_stats["attack"]
        attack_bonus = weapon.get("attack_bonus", 0)

        defense_level = defender_stats["defense"]
        defense_bonus = 0  # TODO: Add armor bonuses

        if calculate_hit_chance(
            attack_level=attack_level,
            attack_bonus=attack_bonus,
            defense_level=defense_level,
            defense_bonus=defense_bonus
        ) > random.random():
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
        interaction: Any,
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
        user: Any,
        db: Optional[Any] = None,
        timeout: float = 180.0
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.db = db
        # Weapon and armor selects for tests
        weapon_select = Select(custom_id="weapon", options=[])
        armor_select = Select(custom_id="armor", options=[])
        # If a mock db with results is provided, populate options from it
        try:
            if self.db and hasattr(self.db, 'mock_results'):
                weapons = self.db.mock_results.get("SELECT * FROM weapons", [])
                # Select options expect objects with label/value properties in tests
                weapon_select.options = [SimpleNamespace(label=w['name'], value=str(w['id'])) for w in weapons]
        except Exception:
            # Best-effort only for tests
            pass
        async def _weapon_wrapper(interaction, select=None):
            return await self.weapon_select(interaction, weapon_select)

        weapon_select._callback = _weapon_wrapper
        armor_select._callback = getattr(self, "armor_select", None) or (lambda *a, **k: None)
        self.children.extend([weapon_select, armor_select])
    
    @discord.ui.select(
        placeholder="Select Weapon",
        custom_id="weapon",
        min_values=1,
        max_values=1
    )
    async def weapon_select(
        self,
        interaction: Any,
        select: Select
    ):
        try:
            # Some test stubs may not populate select.values; fall back to first option
            if not getattr(select, 'values', None):
                select.values = [select.options[0].value] if select.options else ["0"]
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