import discord
from discord.ext import commands
from discord import app_commands, Member
from bot.utils.combat_views_v2 import DuelRequestView, CombatActionView, EquipmentView
from bot.utils.combat_mechanics import (
    process_hit, process_food_heal, process_potion_effect,
    get_combat_log_message
)
import aiosqlite
from datetime import datetime, timedelta
from bot.utils.DButil_v2 import async_get_db_connection

class Duel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_duels = {}  # duel_id -> {state data}

    @app_commands.command(name='dm_register', description='Register for duel matches')
    async def register_user(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        async with await async_get_db_connection() as db:
            await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
            await db.commit()
            
            # Create equipment slots for the user
            await db.execute('INSERT OR IGNORE INTO user_equipment (user_id) VALUES (?)', (user_id,))
            await db.commit()
            
            # Give starter items
            starter_items = [
                ('Bronze Sword', 'weapon', 1),  # weapon_id 1 is bronze sword
                ('Shark', 'food', 5),  # Give 5 sharks
            ]
            for item_name, item_type, quantity in starter_items:
                if item_type == 'weapon':
                    await db.execute('''
                        INSERT OR IGNORE INTO user_inventory (user_id, item_id, quantity)
                        SELECT ?, id, ? FROM weapons WHERE name = ?
                    ''', (user_id, quantity, item_name))
                else:
                    await db.execute('''
                        INSERT OR IGNORE INTO user_inventory (user_id, item_id, quantity)
                        SELECT ?, id, ? FROM items WHERE name = ?
                    ''', (user_id, quantity, item_name))
            
            await db.commit()
        
        await interaction.response.send_message(
            f"{interaction.user.mention}, you have been registered! You received some starter items.",
            ephemeral=True
        )

    @app_commands.command(name='dm_stats', description='View your combat stats and record')
    async def view_stats(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        async with await async_get_db_connection() as db:
            async with db.execute(
                'SELECT * FROM users WHERE user_id = ?', 
                (user_id,)
            ) as cursor:
                user_data = await cursor.fetchone()
        
        if not user_data:
            await interaction.response.send_message(
                "You need to register first with /dm_register",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"Combat Stats for {interaction.user.display_name}",
            color=discord.Color.blue()
        )
        
        # Add combat stats
        stats_text = (
            f"**Attack:** {user_data['attack']}\n"
            f"**Strength:** {user_data['strength']}\n"
            f"**Defense:** {user_data['defense']}\n"
            f"**HP:** {user_data['current_health']}/{user_data['health']}\n"
            f"**Prayer:** {user_data['current_prayer']}/{user_data['prayer_points']}\n"
        )
        embed.add_field(name="Stats", value=stats_text, inline=True)
        
        # Add record
        record_text = (
            f"**Wins:** {user_data['total_wins']}\n"
            f"**Losses:** {user_data['total_losses']}\n"
            f"**W/L Ratio:** {user_data['total_wins']/(user_data['total_losses'] or 1):.2f}\n"
        )
        embed.add_field(name="Record", value=record_text, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='dm_inventory', description='View and manage your inventory')
    async def view_inventory(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        async with await async_get_db_connection() as db:
            # Get inventory items
            async with db.execute('''
                SELECT i.name, i.type, ui.quantity, i.effect_value
                FROM user_inventory ui
                JOIN items i ON ui.item_id = i.id
                WHERE ui.user_id = ?
            ''', (user_id,)) as cursor:
                inventory = await cursor.fetchall()
            
            # Get equipped items
            async with db.execute('''
                SELECT 
                    w.name as weapon,
                    i1.name as head,
                    i2.name as body,
                    i3.name as legs,
                    i4.name as gloves,
                    i5.name as boots
                FROM user_equipment ue
                LEFT JOIN weapons w ON ue.weapon_slot = w.id
                LEFT JOIN items i1 ON ue.head_slot = i1.id
                LEFT JOIN items i2 ON ue.body_slot = i2.id
                LEFT JOIN items i3 ON ue.legs_slot = i3.id
                LEFT JOIN items i4 ON ue.gloves_slot = i4.id
                LEFT JOIN items i5 ON ue.boots_slot = i5.id
                WHERE ue.user_id = ?
            ''', (user_id,)) as cursor:
                equipment = await cursor.fetchone()
        
        # Create embed
        embed = discord.Embed(
            title=f"Inventory for {interaction.user.display_name}",
            color=discord.Color.blue()
        )
        
        # Add equipment section
        equipment_text = "\n".join([
            f"**{slot.title()}:** {item if item else 'None'}"
            for slot, item in equipment.items()
        ])
        embed.add_field(name="Equipment", value=equipment_text, inline=False)
        
        # Group inventory by type
        inv_by_type = {}
        for item in inventory:
            item_type = item['type']
            if item_type not in inv_by_type:
                inv_by_type[item_type] = []
            inv_by_type[item_type].append(item)
        
        # Add inventory sections
        for item_type, items in inv_by_type.items():
            items_text = "\n".join([
                f"**{item['name']}** x{item['quantity']}" + 
                (f" (Heals {item['effect_value']})" if item['type'] == 'food' else "")
                for item in items
            ])
            embed.add_field(
                name=f"{item_type.title()}s",
                value=items_text or "None",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='dm_equip', description='Equip or unequip items')
    async def equip_item(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        async with await async_get_db_connection() as db:
            # Get all available items for each slot
            available_items = {}
            
            # Get weapons
            async with db.execute('''
                SELECT w.id, w.name, w.attack_bonus as bonus
                FROM user_inventory ui
                JOIN weapons w ON ui.item_id = w.id
                WHERE ui.user_id = ? AND ui.quantity > 0
            ''', (user_id,)) as cursor:
                available_items['weapon'] = [dict(row) for row in await cursor.fetchall()]
            
            # Get equipment for other slots
            slots = ['head', 'body', 'legs', 'gloves', 'boots']
            for slot in slots:
                async with db.execute('''
                    SELECT i.id, i.name, i.defense_bonus as bonus
                    FROM user_inventory ui
                    JOIN items i ON ui.item_id = i.id
                    WHERE ui.user_id = ? AND ui.quantity > 0 AND i.slot = ?
                ''', (user_id, slot)) as cursor:
                    available_items[slot] = [dict(row) for row in await cursor.fetchall()]
        
        # Create equipment view
        view = EquipmentView(interaction.user, available_items)
        await interaction.response.send_message(
            "Choose a slot and item to equip:",
            view=view,
            ephemeral=True
        )
        
        # Wait for the selection
        await view.wait()
        if view.selected_slot and view.selected_item:
            async with await async_get_db_connection() as db:
                # Handle unequip
                if view.selected_item == "unequip":
                    await db.execute(
                        f'UPDATE user_equipment SET {view.selected_slot}_slot = NULL WHERE user_id = ?',
                        (user_id,)
                    )
                    await interaction.followup.send(
                        f"Unequipped item from {view.selected_slot} slot.",
                        ephemeral=True
                    )
                else:
                    # Equip new item
                    await db.execute(
                        f'UPDATE user_equipment SET {view.selected_slot}_slot = ? WHERE user_id = ?',
                        (view.selected_item, user_id)
                    )
                    await interaction.followup.send(
                        f"Successfully equipped item to {view.selected_slot} slot.",
                        ephemeral=True
                    )
                await db.commit()

    @app_commands.command(name='dm_duel', description='Challenge another player to a duel')
    async def duel_challenge(
        self,
        interaction: discord.Interaction,
        opponent: Member,
        bet: int = 0
    ):
        if opponent.bot:
            await interaction.response.send_message(
                "You can't duel a bot!",
                ephemeral=True
            )
            return
        
        if opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "You can't duel yourself!",
                ephemeral=True
            )
            return
        
        challenger_id = str(interaction.user.id)
        opponent_id = str(opponent.id)
        
        # Verify both users are registered and have enough gold
        async with await async_get_db_connection() as db:
            async with db.execute(
                'SELECT user_id, gold FROM users WHERE user_id IN (?, ?)',
                (challenger_id, opponent_id)
            ) as cursor:
                users = await cursor.fetchall()
            
            if len(users) < 2:
                await interaction.response.send_message(
                    f"Both players must register with /dm_register first!",
                    ephemeral=True
                )
                return
            
            users_dict = {str(u['user_id']): u['gold'] for u in users}
            if users_dict[challenger_id] < bet or users_dict[opponent_id] < bet:
                await interaction.response.send_message(
                    f"Both players must have at least {bet} gold to place this bet.",
                    ephemeral=True
                )
                return
            
            # Check for active duels
            async with db.execute(
                'SELECT id FROM duels WHERE (user1_id = ? OR user2_id = ? OR user1_id = ? OR user2_id = ?) AND active = 1',
                (challenger_id, challenger_id, opponent_id, opponent_id)
            ) as cursor:
                if await cursor.fetchone():
                    await interaction.response.send_message(
                        "One of the players is already in an active duel!",
                        ephemeral=True
                    )
                    return
        
        # Create duel request view
        view = DuelRequestView(interaction.user, opponent, bet)
        await interaction.response.send_message(
            f"{opponent.mention}, {interaction.user.mention} has challenged you to a duel!\n"
            f"Bet amount: {bet} gold",
            view=view
        )
        
        # Wait for response
        await view.wait()
        
        if view.accepted:
            # Create the duel in DB
            async with await async_get_db_connection() as db:
                cursor = await db.execute('''
                    INSERT INTO duels (
                        user1_id, user2_id, user1_bet, user2_bet,
                        active, current_turn, turn_start_time
                    ) VALUES (?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                ''', (challenger_id, opponent_id, bet, bet, challenger_id))
                duel_id = cursor.lastrowid
                await db.commit()
            
            # Start the duel
            await self._start_duel(
                duel_id,
                interaction.user,
                opponent,
                interaction
            )
        # If declined, view handles the decline message

    async def _start_duel(
        self,
        duel_id: int,
        user1: Member,
        user2: Member,
        interaction: discord.Interaction
    ):
        """Start a duel between two players"""
        # Initialize duel state
        self.active_duels[duel_id] = {
            'user1': user1,
            'user2': user2,
            'current_turn': user1.id,
            'turn_count': 0,
            'last_action': datetime.now()
        }
        
        # Create initial duel state embed
        embed = await self._create_duel_state_embed(duel_id)
        
        # Start first turn
        await interaction.edit_original_response(
            content=f"Duel started! {user1.mention}'s turn!",
            embed=embed
        )
        
        await self._process_turn(duel_id, interaction)

    async def _process_turn(
        self,
        duel_id: int,
        interaction: discord.Interaction
    ):
        """Process a single turn in the duel"""
        duel_state = self.active_duels.get(duel_id)
        if not duel_state:
            return
        
        current_user = duel_state['user1'] if duel_state['current_turn'] == duel_state['user1'].id else duel_state['user2']
        other_user = duel_state['user2'] if current_user == duel_state['user1'] else duel_state['user1']
        
        # Create action view
        view = CombatActionView(current_user, duel_id)
        
        # Update inventory options
        async with await async_get_db_connection() as db:
            async with db.execute('''
                SELECT i.name, i.type, ui.quantity
                FROM user_inventory ui
                JOIN items i ON ui.item_id = i.id
                WHERE ui.user_id = ? AND ui.quantity > 0
            ''', (str(current_user.id),)) as cursor:
                inventory = await cursor.fetchall()
            
            # Update view's inventory options
            view.inventory_select.options = [
                SelectOption(
                    label=f"{item['name']} x{item['quantity']}",
                    value=item['name'],
                    description=f"Type: {item['type']}"
                ) for item in inventory
            ]
        
        # Send turn prompt
        prompt = await interaction.followup.send(
            f"{current_user.mention}'s turn! Choose your action:",
            view=view
        )
        
        # Wait for action selection (with timeout)
        await view.wait()
        
        if not view.action_taken:
            # Turn timed out
            await self._handle_timeout(duel_id, current_user, prompt)
            return
        
        # Process the selected action
        await self._process_action(
            duel_id,
            current_user,
            other_user,
            view.selected_action,
            view.selected_item,
            prompt
        )

    async def _process_action(
        self,
        duel_id: int,
        attacker: Member,
        defender: Member,
        action: str,
        item: Optional[str],
        message: discord.Message
    ):
        """Process a combat action and update the game state"""
        async with await async_get_db_connection() as db:
            # Get attacker's stats and equipment
            async with db.execute('''
                SELECT u.*, w.*, 
                    ue.head_slot, ue.body_slot, ue.legs_slot, 
                    ue.gloves_slot, ue.boots_slot
                FROM users u
                JOIN user_equipment ue ON u.user_id = ue.user_id
                LEFT JOIN weapons w ON ue.weapon_slot = w.id
                WHERE u.user_id = ?
            ''', (str(attacker.id),)) as cursor:
                attacker_data = await cursor.fetchone()
            
            # Get defender's stats and equipment
            async with db.execute('''
                SELECT u.*, w.*, 
                    ue.head_slot, ue.body_slot, ue.legs_slot, 
                    ue.gloves_slot, ue.boots_slot
                FROM users u
                JOIN user_equipment ue ON u.user_id = ue.user_id
                LEFT JOIN weapons w ON ue.weapon_slot = w.id
                WHERE u.user_id = ?
            ''', (str(defender.id),)) as cursor:
                defender_data = await cursor.fetchone()
            
            # Process the action
            action_result = None
            if action in ['attack', 'special']:
                # Process attack
                hit_result = process_hit(
                    attacker_data,
                    defender_data,
                    attacker_data,  # weapon data is included
                    special_attack=(action == 'special')
                )
                
                # Update defender's health
                new_health = defender_data['current_health'] - hit_result['damage']
                await db.execute(
                    'UPDATE users SET current_health = ? WHERE user_id = ?',
                    (max(0, new_health), str(defender.id))
                )
                
                # Log the combat action
                await db.execute('''
                    INSERT INTO combat_log (
                        duel_id, turn_number, attacker_id, defender_id,
                        action_type, weapon_used, damage_dealt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    duel_id,
                    self.active_duels[duel_id]['turn_count'],
                    str(attacker.id),
                    str(defender.id),
                    action,
                    attacker_data['weapon_slot'],
                    hit_result['damage']
                ))
                
                action_result = get_combat_log_message(hit_result, attacker.display_name, defender.display_name)
                
            elif action == 'eat':
                # Process food consumption
                if not item:
                    action_result = "No food selected!"
                else:
                    old_hp = attacker_data['current_health']
                    new_hp, heal_message = process_food_heal(
                        item,
                        old_hp,
                        attacker_data['health']
                    )
                    
                    if new_hp > old_hp:
                        await db.execute(
                            'UPDATE users SET current_health = ? WHERE user_id = ?',
                            (new_hp, str(attacker.id))
                        )
                        
                        # Remove one food item
                        await db.execute('''
                            UPDATE user_inventory
                            SET quantity = quantity - 1
                            WHERE user_id = ? AND item_id = (
                                SELECT id FROM items WHERE name = ?
                            )
                        ''', (str(attacker.id), item))
                        
                        action_result = heal_message
                    else:
                        action_result = "Could not eat that item!"
                
            elif action == 'potion':
                # Process potion use
                if not item:
                    action_result = "No potion selected!"
                else:
                    new_stats, effect_message = process_potion_effect(
                        item,
                        dict(attacker_data)
                    )
                    
                    # Update stats
                    if new_stats != dict(attacker_data):
                        updates = []
                        params = []
                        for stat, value in new_stats.items():
                            if stat in ['attack', 'strength', 'defense']:
                                updates.append(f"{stat} = ?")
                                params.append(value)
                        
                        if updates:
                            params.append(str(attacker.id))
                            await db.execute(
                                f'UPDATE users SET {", ".join(updates)} WHERE user_id = ?',
                                params
                            )
                            
                            # Remove one potion
                            await db.execute('''
                                UPDATE user_inventory
                                SET quantity = quantity - 1
                                WHERE user_id = ? AND item_id = (
                                    SELECT id FROM items WHERE name = ?
                                )
                            ''', (str(attacker.id), item))
                            
                            action_result = effect_message
                    else:
                        action_result = "Could not use that potion!"
                
            elif action == 'prayer':
                # Process prayer toggle
                if not item:
                    action_result = "No prayer selected!"
                else:
                    # Update active prayer
                    await db.execute('''
                        UPDATE duels 
                        SET user1_prayer_active = CASE WHEN user1_id = ? THEN ? ELSE user1_prayer_active END,
                            user2_prayer_active = CASE WHEN user2_id = ? THEN ? ELSE user2_prayer_active END
                        WHERE id = ?
                    ''', (str(attacker.id), item, str(attacker.id), item, duel_id))
                    
                    action_result = f"{attacker.display_name} activated {item}!"
            
            await db.commit()
        
        # Update the message with action result
        embed = await self._create_duel_state_embed(duel_id)
        await message.edit(
            content=action_result,
            embed=embed
        )
        
        # Check if duel is over
        if new_health <= 0:
            await self._end_duel(duel_id, defender, attacker, message)
            return
        
        # Switch turns
        self.active_duels[duel_id]['current_turn'] = defender.id
        self.active_duels[duel_id]['turn_count'] += 1
        self.active_duels[duel_id]['last_action'] = datetime.now()
        
        # Start next turn
        await self._process_turn(duel_id, interaction)

    async def _handle_timeout(
        self,
        duel_id: int,
        current_user: Member,
        message: discord.Message
    ):
        """Handle a turn timeout"""
        other_user = (
            self.active_duels[duel_id]['user2'] 
            if current_user == self.active_duels[duel_id]['user1']
            else self.active_duels[duel_id]['user1']
        )
        
        await message.edit(
            content=f"{current_user.mention} took too long! Forfeit!",
            view=None
        )
        
        await self._end_duel(duel_id, current_user, other_user, message)

    async def _end_duel(
        self,
        duel_id: int,
        loser: Member,
        winner: Member,
        message: discord.Message
    ):
        """End a duel and process rewards"""
        async with await async_get_db_connection() as db:
            # Get duel data
            async with db.execute(
                'SELECT user1_bet, user2_bet FROM duels WHERE id = ?',
                (duel_id,)
            ) as cursor:
                duel_data = await cursor.fetchone()
            
            total_pot = duel_data['user1_bet'] + duel_data['user2_bet']
            
            # Update gold
            await db.execute(
                'UPDATE users SET gold = gold + ? WHERE user_id = ?',
                (total_pot, str(winner.id))
            )
            
            # Update win/loss records
            await db.execute(
                'UPDATE users SET total_wins = total_wins + 1 WHERE user_id = ?',
                (str(winner.id),)
            )
            await db.execute(
                'UPDATE users SET total_losses = total_losses + 1 WHERE user_id = ?',
                (str(loser.id),)
            )
            
            # Mark duel as inactive
            await db.execute(
                'UPDATE duels SET active = 0, winner_id = ? WHERE id = ?',
                (str(winner.id), duel_id)
            )
            
            await db.commit()
        
        # Send victory message
        await message.edit(
            content=(
                f"🏆 {winner.mention} has won the duel against {loser.mention}!\n"
                f"Prize: {total_pot} gold"
            ),
            embed=None,
            view=None
        )
        
        # Clean up duel state
        if duel_id in self.active_duels:
            del self.active_duels[duel_id]

    async def _create_duel_state_embed(self, duel_id: int) -> discord.Embed:
        """Create an embed showing the current duel state"""
        duel_state = self.active_duels[duel_id]
        
        async with await async_get_db_connection() as db:
            # Get user stats
            async with db.execute('''
                SELECT u.*, w.name as weapon_name, d.user1_prayer_active, d.user2_prayer_active
                FROM users u
                JOIN user_equipment ue ON u.user_id = ue.user_id
                LEFT JOIN weapons w ON ue.weapon_slot = w.id
                JOIN duels d ON d.id = ?
                WHERE u.user_id IN (?, ?)
            ''', (
                duel_id,
                str(duel_state['user1'].id),
                str(duel_state['user2'].id)
            )) as cursor:
                players_data = await cursor.fetchall()
        
        embed = discord.Embed(
            title="Duel Status",
            color=discord.Color.gold()
        )
        
        for player_data in players_data:
            user = (
                duel_state['user1']
                if str(duel_state['user1'].id) == player_data['user_id']
                else duel_state['user2']
            )
            
            # Create health bar
            health_percent = player_data['current_health'] / player_data['health']
            health_bars = int(health_percent * 10)
            health_bar = f"{'🟩' * health_bars}{'⬛' * (10 - health_bars)}"
            
            # Create stat block
            stats = (
                f"HP: {player_data['current_health']}/{player_data['health']} {health_bar}\n"
                f"Prayer: {player_data['current_prayer']}/{player_data['prayer_points']}\n"
                f"Weapon: {player_data['weapon_name'] or 'Unarmed'}\n"
                f"Prayer: {player_data['user1_prayer_active'] if user == duel_state['user1'] else player_data['user2_prayer_active'] or 'None'}"
            )
            
            embed.add_field(
                name=f"{user.display_name} {'(Current Turn)' if user.id == duel_state['current_turn'] else ''}",
                value=stats,
                inline=False
            )
        
        return embed

async def setup(bot):
    await bot.add_cog(Duel(bot))