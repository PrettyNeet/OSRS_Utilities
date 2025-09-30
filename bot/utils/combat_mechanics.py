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
    # Base damage from strength
    base_damage = (strength_level * (1 + strength_bonus / 100))
    
    # Apply weapon damage multiplier
    damage = (base_damage * weapon_damage) / 100
    
    # Add randomness within bounds
    min_damage = max(1, int(damage * 0.5))
    max_damage = int(damage * 1.1)
    
    return random.randint(min_damage, max_damage)

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