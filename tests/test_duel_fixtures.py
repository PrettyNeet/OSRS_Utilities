import pytest
from typing import Dict, Any
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

class MockMember:
    _id_counter = 10000

    def __init__(self, id: int | None = None, name: str | None = None):
        if id is None:
            id = MockMember._id_counter
            MockMember._id_counter += 1
        if name is None:
            name = f"User{id}"
        self.id = id
        self.mention = f"<@{id}>"
        self.display_name = name
        self.display_avatar = MagicMock()
        self.display_avatar.url = "http://example.com/avatar.png"
        # default to not a bot
        self.bot = False

def test_weapons() -> Dict[str, Dict[str, Any]]:
    """Predefined weapons for testing (callable helper).

    Some tests import and call this directly. A pytest fixture with the
    same name is also provided below for tests that request it as a
    function parameter.
    """
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

def test_items() -> Dict[str, Dict[str, Any]]:
    """Predefined items for testing (callable helper).

    See note in `test_weapons` about dual usage.
    """
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

def test_user_stats() -> Dict[str, Dict[str, Any]]:
    """Predefined user stats for testing (callable helper).

    See note in `test_weapons` about dual usage.
    """
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

_LAST_INTERACTION_USER: MockMember | None = None
_LAST_INTERACTION_CONSUMED = False
_LAST_CREATED_MEMBER: MockMember | None = None

def mock_member() -> MockMember:
    """Create a mock Discord member.

    The first call after mock_interaction() will return the interaction's
    user so tests that expect interaction.user and a separate mock_member()
    to reference the same user will work.
    """
    global _LAST_INTERACTION_USER, _LAST_INTERACTION_CONSUMED
    if _LAST_INTERACTION_USER is not None and not _LAST_INTERACTION_CONSUMED:
        _LAST_INTERACTION_CONSUMED = True
        member = _LAST_INTERACTION_USER
        global _LAST_CREATED_MEMBER
        _LAST_CREATED_MEMBER = member
        return member
    member = MockMember()
    _LAST_CREATED_MEMBER = member
    return member

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
        # user will be set by mock_interaction() so tests can control identity
        self.user = None
        # Provide a mock client attribute for tests that construct cogs with
        # `Duel(bot=interaction.client)`
        self.client = MagicMock()

def mock_interaction() -> MockInteraction:
    """Create a mock Discord interaction"""
    inter = MockInteraction()
    global _LAST_INTERACTION_USER, _LAST_INTERACTION_CONSUMED
    user = MockMember()
    inter.user = user
    inter.client = MagicMock()
    _LAST_INTERACTION_USER = user
    _LAST_INTERACTION_CONSUMED = False
    return inter

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

def setup_mock_db(mock_db, weapons_fixture=None, items_fixture=None, stats_fixture=None):
    """Setup mock database with test data

    Accept either explicit fixture data or fall back to the module fixtures above.
    """
    # Allow callers to pass in fixture data or use module helpers
    if weapons_fixture is None:
        weapons = test_weapons()
    else:
        weapons = weapons_fixture

    if items_fixture is None:
        items = test_items()
    else:
        items = items_fixture

    if stats_fixture is None:
        stats = test_user_stats()
    else:
        stats = stats_fixture

    def _setup(queries_results: Dict[str, list] = None):
        # Default query results using test fixtures
        default_results = {
            "SELECT * FROM weapons": [
                dict(w) for w in weapons.values()
            ],
            "SELECT * FROM items": [
                dict(i) for i in items.values()
            ],
        }

        # Use the last-created mock members to populate user results if available
        try:
            u1 = _LAST_INTERACTION_USER
            u2 = _LAST_CREATED_MEMBER
            if u1 and u2:
                default_results["SELECT * FROM users WHERE user_id = ?"] = [
                    {"user_id": str(u1.id), **stats["maxed_main"]}
                ]
                default_results["SELECT user_id, gold FROM users WHERE user_id IN (?, ?)"] = [
                    {"user_id": str(u1.id), "gold": 100000},
                    {"user_id": str(u2.id), "gold": 100000}
                ]
        except Exception:
            # Fallback to static ids
            default_results["SELECT * FROM users WHERE user_id = ?"] = [
                dict(user_id="12345", **stats["maxed_main"])
            ]
            default_results["SELECT user_id, gold FROM users WHERE user_id IN (?, ?)"] = [
                {"user_id": "12345", "gold": 100000},
                {"user_id": "67890", "gold": 100000}
            ]

        # Update with any custom query results
        if queries_results:
            default_results.update(queries_results)

        # Set all results in mock db
        for query, results in default_results.items():
            mock_db.set_results(query, results)

        # Expose the configured mock DB globally so code under test that
        # calls async_get_db_connection() can pick it up during tests.
        global GLOBAL_MOCK_DB
        GLOBAL_MOCK_DB = mock_db

        return mock_db

    # Return the configured mock db instance (call _setup with no overrides)
    return _setup()

# Provide pytest fixtures with the same names so tests can request them
# via function parameters. We intentionally use different function names
# for the fixture providers to avoid shadowing the callable helpers above.
@pytest.fixture(scope="module", name="test_weapons")
def _fixture_test_weapons():
    return test_weapons()


@pytest.fixture(scope="module", name="test_items")
def _fixture_test_items():
    return test_items()


@pytest.fixture(scope="module", name="test_user_stats")
def _fixture_test_user_stats():
    return test_user_stats()
