from typing import Dict, Optional, Tuple
import random
import math
from datetime import datetime
import discord

def calculate_hit_chance(
    attack_level: int,
    attack_bonus: int,
    defense_level: int,
    defense_bonus: int
) -> float:
    """Calculate hit chance based on OSRS mechanics"""
    # Base accuracy from attack level
    base_accuracy = attack_level * (1 + attack_bonus / 100)
    
    # Base defense roll
    defense_roll = defense_level * (1 + defense_bonus / 100)
    
    # Calculate hit chance with diminishing returns
    if defense_roll == 0:
        return min(0.95, base_accuracy / 100)
    
    hit_chance = base_accuracy / (base_accuracy + defense_roll)
    return min(0.95, max(0.05, hit_chance))

def calculate_damage(
    strength_level: int,
    strength_bonus: int,
    weapon_damage: int
) -> int:
    """Calculate damage based on strength and weapon"""
    # Aim for a damage value roughly around the weapon's listed damage
    # while letting strength and strength_bonus give modest scaling.
    # This keeps values reasonable for tests (e.g., 99 str + bonuses shouldn't produce huge multipliers).
    str_factor = (strength_level / 99.0)  # 0..1
    bonus_factor = (strength_bonus / 100.0) * 0.05  # small extra from gear

    multiplier = 0.5 + (str_factor * 0.3) + bonus_factor
    damage = max(1.0, weapon_damage * multiplier)

    # Return a stable integer damage value (ceiling) so boosted strength reliably
    # yields an increased damage value in tests.
    return max(1, int(math.ceil(damage)))

def calculate_special_attack(
    weapon_name: str,
    base_damage: int,
    special_cost: int
) -> int:
    """Calculate special attack damage based on weapon"""
    if weapon_name == "Granite Maul":
        # 50% chance for big damage
        if random.random() < 0.5:
            return int(base_damage * 1.75)
        return int(base_damage * 1.25)
    
    elif weapon_name == "Dragon Scimitar":
        # 35% chance to ignore defense
        if random.random() < 0.35:
            return int(base_damage * 1.5)
        return base_damage
    
    # Default 25% boost for unhandled specials
    return int(base_damage * 1.25)

def apply_prayer_bonuses(
    stats: Dict[str, int],
    prayer_name: str
) -> Dict[str, int]:
    """Apply prayer bonuses to combat stats"""
    updated_stats = stats.copy()
    
    if prayer_name == "Piety":
        updated_stats["attack"] = int(stats["attack"] * 1.2)
        updated_stats["strength"] = int(stats["strength"] * 1.23)
        updated_stats["defense"] = int(stats["defense"] * 1.25)
    
    elif prayer_name == "Ultimate Strength":
        updated_stats["strength"] = int(stats["strength"] * 1.15)
    
    elif prayer_name == "Steel Skin":
        updated_stats["defense"] = int(stats["defense"] * 1.15)
    
    return updated_stats

def calculate_combat_stats(
    base_stats: Dict[str, int],
    equipment: Dict[str, Dict[str, int]],
    active_prayers: Optional[list] = None
) -> Dict[str, int]:
    """Calculate final combat stats with equipment and prayers"""
    stats = base_stats.copy()
    
    # Apply equipment bonuses
    for item in equipment.values():
        if item:
            stats["attack"] += item.get("attack_bonus", 0)
            stats["strength"] += item.get("strength_bonus", 0)
            stats["defense"] += item.get("defense_bonus", 0)
    
    # Apply prayer effects
    if active_prayers:
        for prayer in active_prayers:
            stats = apply_prayer_bonuses(stats, prayer)
    
    return stats


def process_hit(attacker: Dict, defender: Dict, weapon: Dict, special_attack: bool = False) -> Dict:
    """Simulate a hit from attacker to defender and return result details.

    Expected return keys:
    - damage: int
    - hit: bool
    - was_special: bool
    - was_crit: bool
    """
    # Extract simplified stats (fall back to defaults)
    atk_level = int(attacker.get("attack", 1))
    str_level = int(attacker.get("strength", 1))
    def_level = int(defender.get("defense", 1))

    atk_bonus = int(weapon.get("attack_bonus", 0)) if weapon else 0
    str_bonus = int(weapon.get("strength_bonus", 0)) if weapon else 0
    weapon_damage = int(weapon.get("damage", 1)) if weapon else 1

    # Determine hit chance and resolve hit
    hit_chance = calculate_hit_chance(
        attack_level=atk_level,
        attack_bonus=atk_bonus,
        defense_level=def_level,
        defense_bonus=0
    )

    hit = random.random() < hit_chance

    # Base damage calculation
    if hit:
        base = calculate_damage(
            strength_level=str_level,
            strength_bonus=str_bonus,
            weapon_damage=weapon_damage
        )

        # Apply special attack modifier
        if special_attack and weapon:
            damage = calculate_special_attack(weapon.get("name", ""), base, weapon.get("special_attack_cost", 0))
            was_special = True
        else:
            damage = base
            was_special = False

        # small chance for critical (extra 25% damage)
        was_crit = random.random() < 0.05
        if was_crit:
            damage = int(damage * 1.25)
    else:
        damage = 0
        was_special = False
        was_crit = False

    return {
        "damage": int(damage),
        "hit": hit,
        "was_special": was_special,
        "was_crit": was_crit,
    }


def process_food_heal(item_name: str, current_hp: int, max_hp: int) -> Tuple[int, str]:
    """Process eating a food item. Returns (new_hp, message)."""
    # Simple heal mapping for common foods
    heals = {
        "Shark": 20,
        "Lobster": 12,
        "Swordfish": 14,
        "Monkfish": 16,
        "Anglerfish": 22,
        "Manta Ray": 22,
        "Tuna": 8
    }

    heal = heals.get(item_name, 10)
    new_hp = min(max_hp, current_hp + heal)
    msg = f"{item_name} consumed: healed {new_hp - current_hp} HP."
    return new_hp, msg


def process_potion_effect(item_name: str, stats: Dict) -> Tuple[Dict, str]:
    """Apply a potion effect to stats and return (new_stats, message).

    This function returns a new stats dict (does not mutate input).
    """
    new_stats = dict(stats)
    name = item_name.lower()

    if "super combat" in name or "super_combat" in name:
        # temporary +5 to attack/strength/defense
        new_stats["attack"] = int(new_stats.get("attack", 0) + 5)
        new_stats["strength"] = int(new_stats.get("strength", 0) + 5)
        new_stats["defense"] = int(new_stats.get("defense", 0) + 5)
        return new_stats, "Used Super Combat Potion: +5 to attack/strength/defense."

    # default: no effect
    return stats, "No effect from that potion."


def get_combat_log_message(hit_result: Dict, attacker_name: str, defender_name: str) -> str:
    """Compose a readable combat log message from a hit result."""
    if not hit_result.get("hit") or hit_result.get("damage", 0) == 0:
        return f"{attacker_name} tried to hit {defender_name} but missed!"

    dmg = hit_result.get("damage", 0)
    parts = [f"{attacker_name} hits {defender_name} for {dmg} damage!"]
    if hit_result.get("was_special"):
        parts.append("(special)")
    if hit_result.get("was_crit"):
        parts.append("(critical)")

    return " ".join(parts)