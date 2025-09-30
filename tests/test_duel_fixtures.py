import pytest
from typing import Dict, Any
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

class MockMember:
    def __init__(self, id: int, name: str):
        self.id = id
        self.mention = f"<@{id}>"
        self.display_name = name
        self.display_avatar = MagicMock()
        self.display_avatar.url = "http://example.com/avatar.png"

@pytest.fixture
def test_weapons() -> Dict[str, Dict[str, Any]]:
    """Predefined weapons for testing"""
    return {
        "dragon_scimitar": {
            "id": 1,
            "name": "Dragon Scimitar",
            "damage": 25,
            "speed": 4,
            "cost": 5000,
            "attack_style": "slash",
            "attack_bonus": 67,
            "strength_bonus": 66,
            "special_attack": "Slice and Dice",
            "special_attack_cost": 25,
            "weapon_type": "melee"
        },
        "granite_maul": {
            "id": 2,
            "name": "Granite Maul",
            "damage": 35,
            "speed": 7,
            "cost": 15000,
            "attack_style": "crush",
            "attack_bonus": 81,
            "strength_bonus": 81,
            "special_attack": "Quick Smash",
            "special_attack_cost": 50,
            "weapon_type": "melee"
        }
    }

@pytest.fixture
def test_items() -> Dict[str, Dict[str, Any]]:
    """Predefined items for testing"""
    return {
        "shark": {
            "id": 1,
            "name": "Shark",
            "type": "food",
            "slot": None,
            "cost": 1000,
            "effect_type": "heal",
            "effect_value": 20,
            "attack_bonus": 0,
            "defense_bonus": 0,
            "strength_bonus": 0,
            "prayer_bonus": 0
        },
        "super_combat": {
            "id": 2,
            "name": "Super Combat Potion",
            "type": "potion",
            "slot": None,
            "cost": 2000,
            "effect_type": "boost",
            "effect_value": 5,
            "attack_bonus": 0,
            "defense_bonus": 0,
            "strength_bonus": 0,
            "prayer_bonus": 0
        },
        "neitz_helm": {
            "id": 3,
            "name": "Helm of Neitiznot",
            "type": "equipment",
            "slot": "head",
            "cost": 5000,
            "effect_type": None,
            "effect_value": 0,
            "attack_bonus": 3,
            "defense_bonus": 3,
            "strength_bonus": 3,
            "prayer_bonus": 2
        }
    }

@pytest.fixture
def test_user_stats() -> Dict[str, Dict[str, Any]]:
    """Predefined user stats for testing"""
    return {
        "maxed_main": {
            "attack": 99,
            "strength": 99,
            "defense": 99,
            "prayer": 99,
            "health": 99,
            "current_health": 99,
            "prayer_points": 99,
            "current_prayer": 99,
            "gold": 100000,
            "total_wins": 10,
            "total_losses": 5
        },
        "pure": {
            "attack": 60,
            "strength": 99,
            "defense": 1,
            "prayer": 52,
            "health": 99,
            "current_health": 99,
            "prayer_points": 52,
            "current_prayer": 52,
            "gold": 50000,
            "total_wins": 5,
            "total_losses": 2
        }
    }

@pytest.fixture
def mock_member() -> MockMember:
    """Create a mock Discord member"""
    return MockMember(12345, "TestUser")

class MockInteraction:
    def __init__(self):
        self.response = AsyncMock()
        self.response.send_message = AsyncMock()
        self.response.edit_message = AsyncMock()
        self.response.defer = AsyncMock()
        self.followup = AsyncMock()
        self.followup.send = AsyncMock()
        self.message = MagicMock()
        self.message.content = ""
        self.user = MockMember(12345, "TestUser")

@pytest.fixture
def mock_interaction() -> MockInteraction:
    """Create a mock Discord interaction"""
    return MockInteraction()

@pytest.fixture
def mock_db():
    """Create a mock database connection with predefined data"""
    class MockCursor:
        def __init__(self, results=None):
            self.results = results or []
            self.row_idx = 0
            self.executed_queries = []
            self.executed_params = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def fetchone(self):
            if self.row_idx < len(self.results):
                row = self.results[self.row_idx]
                self.row_idx += 1
                return row
            return None

        async def fetchall(self):
            return self.results

    class MockDB:
        def __init__(self):
            self.executed_queries = []
            self.executed_params = []
            self.mock_results = {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        def set_results(self, query, results):
            self.mock_results[query] = results

        async def execute(self, query, params=None):
            self.executed_queries.append(query)
            self.executed_params.append(params)
            return MockCursor(self.mock_results.get(query, []))

        async def commit(self):
            pass

        async def close(self):
            pass

    return MockDB()

@pytest.fixture
def setup_mock_db(mock_db, test_weapons, test_items, test_user_stats):
    """Setup mock database with test data"""
    def _setup(queries_results: Dict[str, list] = None):
        # Default query results using test fixtures
        default_results = {
            "SELECT * FROM weapons": [
                dict(id=w["id"], **w) for w in test_weapons.values()
            ],
            "SELECT * FROM items": [
                dict(id=i["id"], **i) for i in test_items.values()
            ],
            "SELECT * FROM users WHERE user_id = ?": [
                dict(user_id="12345", **test_user_stats["maxed_main"])
            ]
        }
        
        # Update with any custom query results
        if queries_results:
            default_results.update(queries_results)
        
        # Set all results in mock db
        for query, results in default_results.items():
            mock_db.set_results(query, results)
        
        return mock_db
    
    return _setup