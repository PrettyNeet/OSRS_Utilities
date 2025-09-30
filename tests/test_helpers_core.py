import pytest

from bot.utils import helpers


def test_skill_interp_bounds_and_values():
    # level 1 (min) and 99 (max) should produce values within [0,1]
    v_min = helpers.skill_interp(100, 200, 1)
    v_mid = helpers.skill_interp(100, 200, 50)
    v_max = helpers.skill_interp(100, 200, 99)
    assert 0 <= v_min <= 1
    assert 0 <= v_mid <= 1
    assert 0 <= v_max <= 1


def test_generate_estimated_yield_error_when_chance_is_one():
    # Construct inputs that make skill_interp return 1 (high_cts_final large)
    farming_level = 99
    low_cts = 100
    high_cts = 255  # leads to high_cts_final + 1 == 256 -> skill_interp -> 1
    harvest_lives = 4
    item_bonus = 0
    diary_bonus = 0
    attas_bonus = 0

    res = helpers.generate_estimated_yield(farming_level, low_cts, high_cts, harvest_lives, item_bonus, diary_bonus, attas_bonus)
    assert isinstance(res, str) and 'Error' in res


def test_generate_estimated_yield_numeric():
    farming_level = 50
    low_cts = 100
    high_cts = 200
    harvest_lives = 4
    item_bonus = 0.1
    diary_bonus = 2
    attas_bonus = 0.05

    res = helpers.generate_estimated_yield(farming_level, low_cts, high_cts, harvest_lives, item_bonus, diary_bonus, attas_bonus)
    assert isinstance(res, float)
    assert res > 0


def test_format_profit_table_basic():
    rows = [{"Herb": "Guam", "Seed Price": 10, "Grimy Herb Price": 100, "Potential Yield": 2, "Profit per Seed": 45, "Profit per Run": 90}]
    table = helpers.format_profit_table(rows)
    assert 'Herb | Seed Price | Grimy Herb Price' in table
    assert 'Guam' in table
    assert '90' in table
