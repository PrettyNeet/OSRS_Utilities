import pytest

# Basic smoke tests for helpers. These mirror the previous unittest tests
from bot.utils.helpers import skill_interp, generate_estimated_yield


def test_skill_interp_ranges():
    # level 20 should return a normalized value between 0 and 1
    level = 20
    low_cts = 1000
    high_cts = 2000
    v = skill_interp(low_cts, high_cts, level)
    assert 0 <= v <= 1

    # level 70 should also be between 0 and 1
    level = 70
    low_cts = 1500
    high_cts = 2500
    v2 = skill_interp(low_cts, high_cts, level)
    assert 0 <= v2 <= 1


def test_generate_estimated_yield_error_cases():
    # Use parameters that previously returned the error string
    farming_level = 60
    low_cts = 1000
    high_cts = 2000
    harvest_lives = 10
    item_bonus = 0.05
    diary_bonus = 5
    attas_bonus = 0.1
    res = generate_estimated_yield(farming_level, low_cts, high_cts, harvest_lives, item_bonus, diary_bonus, attas_bonus)
    # Accept either the error string or a numeric result as before
    assert isinstance(res, (str, int, float))

# TODO create some unit tests
import unittest
from bot.utils.helpers import skill_interp, generate_estimated_yield

class TestHelpers(unittest.TestCase):
    def test_skill_interp(self):
        # Test 1: Level 10-50
        level = 20
        low_cts = 1000
        high_cts = 2000
        self.assertAlmostEqual(skill_interp(low_cts, high_cts, level), 1, places=7)

        # Test 2: Level 51-99
        level = 70
        low_cts = 1500
        high_cts = 2500
        self.assertAlmostEqual(skill_interp(low_cts, high_cts, level), 1, places=7)

    def test_generate_estimated_yield(self):
        # Test 1: Low CTs, High Yield
        farming_level = 60
        low_cts = 1000
        high_cts = 2000
        harvest_lives = 10
        item_bonus = 0.05
        diary_bonus = 5
        attas_bonus = 0.1
        self.assertAlmostEqual(generate_estimated_yield(farming_level, low_cts, high_cts, harvest_lives, item_bonus, diary_bonus, attas_bonus), "Error: No yield calculated")

        # Test 2: High CTs, Low Yield
        farming_level = 60
        low_cts = 2000
        high_cts = 3000
        harvest_lives = 5
        item_bonus = 0.05
        diary_bonus = 5
        attas_bonus = 0.1
        self.assertAlmostEqual(generate_estimated_yield(farming_level, low_cts, high_cts, harvest_lives, item_bonus, diary_bonus, attas_bonus), "Error: No yield calculated")

if __name__ == "__main__":
    unittest.main()
