import pytest
from bot.utils.combat_mechanics import calculate_hit_chance, calculate_damage, calculate_special_attack
from tests.test_duel_fixtures import test_weapons, test_items, test_user_stats

def test_hit_chance_calculation():
    """Test hit chance calculations for combat mechanics"""
    # Test maxed main vs maxed main
    attacker = test_user_stats()["maxed_main"]
    defender = test_user_stats()["maxed_main"]
    weapon = test_weapons()["dragon_scimitar"]
    
    # Calculate hit chance with equal stats
    hit_chance = calculate_hit_chance(
        attack_level=attacker["attack"],
        attack_bonus=weapon["attack_bonus"],
        defense_level=defender["defense"],
        defense_bonus=0  # No armor in this test case
    )
    
    # With equal maxed stats, hit chance should be reasonable
    assert 0.6 <= hit_chance <= 0.8, "Hit chance should be balanced for equal maxed stats"
    
    # Test pure vs maxed main (low defense vs high defense)
    pure_attacker = test_user_stats()["pure"]
    pure_hit_chance = calculate_hit_chance(
        attack_level=pure_attacker["attack"],
        attack_bonus=weapon["attack_bonus"],
        defense_level=defender["defense"],
        defense_bonus=0
    )
    
    # Pure should have lower hit chance against maxed main
    assert pure_hit_chance < hit_chance, "Pure should have lower accuracy vs maxed main"
    assert pure_hit_chance > 0.3, "Pure should still have reasonable hit chance"

def test_damage_calculation():
    """Test damage calculations for combat mechanics"""
    # Test maxed main damage
    attacker = test_user_stats()["maxed_main"]
    weapon = test_weapons()["dragon_scimitar"]
    
    # Calculate damage with strength bonus
    base_damage = calculate_damage(
        strength_level=attacker["strength"],
        strength_bonus=weapon["strength_bonus"],
        weapon_damage=weapon["damage"]
    )
    
    # Test damage range is reasonable for maxed stats
    assert 20 <= base_damage <= weapon["damage"], "Damage should be within weapon's range"
    
    # Test with strength boosting item
    potion = test_items()["super_combat"]
    boosted_damage = calculate_damage(
        strength_level=attacker["strength"] + potion["effect_value"],
        strength_bonus=weapon["strength_bonus"],
        weapon_damage=weapon["damage"]
    )
    
    assert boosted_damage > base_damage, "Boosted strength should increase damage"

def test_special_attack():
    """Test special attack calculations"""
    # Test granite maul special
    attacker = test_user_stats()["maxed_main"]
    weapon = test_weapons()["granite_maul"]
    
    # Calculate special attack damage
    special_damage = calculate_special_attack(
        weapon_name=weapon["name"],
        base_damage=calculate_damage(
            strength_level=attacker["strength"],
            strength_bonus=weapon["strength_bonus"],
            weapon_damage=weapon["damage"]
        ),
        special_cost=weapon["special_attack_cost"]
    )
    
    # Granite maul special should do increased damage
    assert special_damage > weapon["damage"], "Special attack should deal bonus damage"
    assert special_damage <= weapon["damage"] * 2, "Special attack damage should be reasonably balanced"

def test_combat_mechanics_edge_cases():
    """Test edge cases in combat mechanics"""
    attacker = test_user_stats()["pure"]
    defender = test_user_stats()["maxed_main"]
    weapon = test_weapons()["dragon_scimitar"]
    
    # Test hit chance with extreme defense bonus
    hit_chance = calculate_hit_chance(
        attack_level=attacker["attack"],
        attack_bonus=weapon["attack_bonus"],
        defense_level=defender["defense"],
        defense_bonus=1000  # Unrealistically high defense bonus
    )
    
    # Should still have some chance to hit, even if very low
    assert hit_chance > 0, "Should never have 0% hit chance"
    assert hit_chance < 0.1, "Should have very low hit chance against extreme defense"
    
    # Test damage with minimum strength
    min_damage = calculate_damage(
        strength_level=1,
        strength_bonus=0,
        weapon_damage=weapon["damage"]
    )
    
    assert min_damage > 0, "Should always do some damage"
    assert min_damage < weapon["damage"], "Minimum damage should be less than max"