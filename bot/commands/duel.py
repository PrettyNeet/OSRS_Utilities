import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from bot.utils.DButil import get_db_path, get_db_connection, initialize_db, add_predefined_weapons, async_get_db_connection

# Ensure DB is initialized on import (safe)
initialize_db()
add_predefined_weapons()


class Duel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='dm_register', description='Register for duel economy')
    async def register_user(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        db = await async_get_db_connection()
        await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        await db.commit()
        await db.close()
        await interaction.response.send_message(f"{interaction.user.mention}, you have been registered!", ephemeral=True)

    @app_commands.command(name='dm_balance', description='Check your duel balance')
    async def check_balance(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        db = await async_get_db_connection()
        async with db.execute('SELECT gold FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
        await db.close()

        if row:
            gold = row[0]
            await interaction.response.send_message(f"{interaction.user.mention}, you have {gold} gold.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{interaction.user.mention}, you need to register first by using /dm_register.", ephemeral=True)
    
    @commands.command(name='dm_storage')
    async def view_storage(self, ctx):
        user_id = ctx.author.id
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT gold, weapons, gear FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            gold, weapons, gear = user_data
            storage_message = f"**Your Storage**\n\nGold: {gold}\nWeapons: {weapons}\nGear: {gear}"
        else:
            storage_message = "You don't have any stored items."

        await ctx.send(storage_message)
        
    @commands.command(name='dm_shop')
    async def show_shop(self, ctx):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM weapons')
        weapons = c.fetchall()
        conn.close()
        shop_list = "\n".join([f"{weapon['name']} (Damage: {weapon['damage']}, Speed: {weapon['speed']}) - {weapon['cost']} gold" for weapon in weapons])
        await ctx.send(f"Available weapons:\n{shop_list}")

    @commands.command(name='dm_buy')
    async def buy_weapon(self, ctx, weapon_name: str):
        user_id = str(ctx.author.id)
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT gold FROM users WHERE user_id = ?', (user_id,))
        user_data = c.fetchone()

        if user_data:
            c.execute('SELECT * FROM weapons WHERE name = ?', (weapon_name,))
            weapon = c.fetchone()
            if weapon and user_data['gold'] >= weapon['cost']:
                c.execute('UPDATE users SET gold = gold - ? WHERE user_id = ?', (weapon['cost'], user_id))
                c.execute('INSERT INTO user_gear (user_id, weapon_id) VALUES (?, ?)', (user_id, weapon['id']))
                conn.commit()
                await ctx.send(f"{ctx.author.mention}, you have bought {weapon_name}!")
            else:
                await ctx.send(f"{ctx.author.mention}, you don't have enough gold or the weapon does not exist.")
        else:
            await ctx.send(f"{ctx.author.mention}, you need to register first by using /dm_register.")

        conn.close()

    @commands.command(name='dm_equip')
    async def equip_weapon(self, ctx, weapon_name: str):
        user_id = str(ctx.author.id)
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
        SELECT wg.id FROM user_gear wg
        JOIN weapons w ON wg.weapon_id = w.id
        WHERE wg.user_id = ? AND w.name = ?
        ''', (user_id, weapon_name))
        weapon = c.fetchone()

        if weapon:
            c.execute('UPDATE user_gear SET equipped = 0 WHERE user_id = ?', (user_id,))
            c.execute('UPDATE user_gear SET equipped = 1 WHERE id = ?', (weapon['id'],))
            conn.commit()
            await ctx.send(f"{ctx.author.mention}, you have equipped {weapon_name}.")
        else:
            await ctx.send(f"{ctx.author.mention}, you do not own this weapon.")

        conn.close()

    @commands.command(name='dm_duel')
    async def start_duel(self, ctx, opponent: discord.Member, bet: int):
        user1_id = str(ctx.author.id)
        user2_id = str(opponent.id)
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT gold FROM users WHERE user_id = ?', (user1_id,))
        user1_data = c.fetchone()
        c.execute('SELECT gold FROM users WHERE user_id = ?', (user2_id,))
        user2_data = c.fetchone()

        if user1_data and user2_data and user1_data['gold'] >= bet and user2_data['gold'] >= bet:
            c.execute('INSERT INTO duels (user1_id, user2_id, user1_bet, user2_bet) VALUES (?, ?, ?, ?)', (user1_id, user2_id, bet, bet))
            conn.commit()
            await ctx.send(f"{ctx.author.mention} has challenged {opponent.mention} to a duel with a bet of {bet} gold each!")
        else:
            await ctx.send(f"{ctx.author.mention}, one of you does not have enough gold or is not registered.")

        conn.close()


async def setup(bot):
    await bot.add_cog(Duel(bot))
