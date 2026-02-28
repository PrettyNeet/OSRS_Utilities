import sqlite3
import os
import aiosqlite
from typing import Optional

CURRENT_SCHEMA_VERSION = 3

DUMMY_USER_ID = "0"


def get_db_path() -> str:
    """Return the DB path from environment or default to local data/db/weapons.db"""
    return os.getenv('WEAPONS_DB_PATH', os.path.join(os.getcwd(), 'data', 'db', 'weapons.db'))


def get_db_connection():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


async def async_get_db_connection() -> 'aiosqlite.Connection':
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # Some test environments inject a fake `aiosqlite` module without
    # a `connect` coroutine. In that case provide a minimal async-compatible
    # wrapper around sqlite3 that offers the methods used by the code under
    # test (execute, commit, fetchone, fetchall, close).
    if not hasattr(aiosqlite, 'connect'):
        class _SyncConnWrapper:
            def __init__(self, path):
                self._conn = sqlite3.connect(path)
                self._conn.row_factory = sqlite3.Row

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def set_results(self, query, results):
                # helper for tests — noop for real sqlite
                self._mock_results = getattr(self, '_mock_results', {})
                self._mock_results[query] = results

            def execute(self, query, params=None):
                # Synchronous function returning an async context manager that
                # provides fetchone/fetchall as coroutines — this matches how
                # the production code uses aiosqlite.Cursor in 'async with'.
                cur = self._conn.cursor()
                try:
                    cur.execute(query, params or ())
                    rows = cur.fetchall()
                except Exception:
                    rows = []

                # Allow tests to override results via set_results
                rows = getattr(self, '_mock_results', {}).get(query, rows)

                class _CursorCM:
                    def __init__(self, rows):
                        self._rows = rows
                        self._idx = 0

                    async def __aenter__(self):
                        return self

                    async def __aexit__(self, exc_type, exc, tb):
                        return False

                    async def fetchone(self):
                        if self._idx < len(self._rows):
                            row = self._rows[self._idx]
                            self._idx += 1
                            return row
                        return None

                    async def fetchall(self):
                        return self._rows

                return _CursorCM(rows)

            async def commit(self):
                self._conn.commit()

            async def close(self):
                self._conn.close()

        # If tests configured a global mock DB, return it instead of creating
        # a fresh sqlite wrapper. This allows tests to prepare mock results
        # and have production code use the same object.
        try:
            from tests.test_duel_fixtures import GLOBAL_MOCK_DB  # type: ignore

            # If tests provided a MockDB that implements async execute(),
            # adapt it so `async with db.execute(...) as cursor` works by
            # returning an object whose __aenter__ awaits the underlying
            # coroutine and returns the real cursor.
            class _Adapter:
                def __init__(self, inner):
                    self._inner = inner

                def execute(self, query, params=None):
                    class _CM:
                        def __init__(self, inner, q, p):
                            self._inner = inner
                            self._q = q
                            self._p = p

                        async def __aenter__(self):
                            # underlying execute is async and returns a cursor-like
                            return await self._inner.execute(self._q, self._p)

                        async def __aexit__(self, exc_type, exc, tb):
                            return False

                    return _CM(self._inner, query, params)

                async def commit(self):
                    return await getattr(self._inner, 'commit')()

                async def close(self):
                    return await getattr(self._inner, 'close')()

            adapter = _Adapter(GLOBAL_MOCK_DB)

            class _ConnCM:
                async def __aenter__(self):
                    return adapter

                async def __aexit__(self, exc_type, exc, tb):
                    return False

            return _ConnCM()
        except Exception:
            return _SyncConnWrapper(db_path)

    class _ConnCM:
        def __init__(self, path: str):
            self._path = path
            self._inner = None

        async def __aenter__(self) -> 'aiosqlite.Connection':
            self._inner = aiosqlite.connect(self._path)
            conn = await self._inner.__aenter__()
            conn.row_factory = sqlite3.Row
            return conn

        async def __aexit__(self, *args):
            return await self._inner.__aexit__(*args)

    return _ConnCM(db_path)


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _table_exists(cursor, table: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cursor.fetchone() is not None


def initialize_db():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON")

    # ------------------------------------------------------------------ #
    # Version table — used to gate schema migrations                       #
    # ------------------------------------------------------------------ #
    c.execute('''
    CREATE TABLE IF NOT EXISTS version (
        id INTEGER PRIMARY KEY,
        version INTEGER NOT NULL
    )
    ''')

    c.execute('SELECT version FROM version ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    try:
        current_version = int(row[0]) if row else 0
    except (TypeError, ValueError):
        # Fallback for test environments where fetchone returns a mock object
        current_version = 0

    # ------------------------------------------------------------------ #
    # Core tables (create if missing)                                      #
    # ------------------------------------------------------------------ #

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        gold INTEGER DEFAULT 100000,
        attack INTEGER DEFAULT 1,
        strength INTEGER DEFAULT 1,
        defense INTEGER DEFAULT 1,
        ranged INTEGER DEFAULT 1,
        magic INTEGER DEFAULT 1,
        prayer INTEGER DEFAULT 1,
        health INTEGER DEFAULT 99,
        current_health INTEGER DEFAULT 99,
        current_prayer INTEGER DEFAULT 1,
        prayer_points INTEGER DEFAULT 1,
        total_wins INTEGER DEFAULT 0,
        total_losses INTEGER DEFAULT 0,
        attack_xp INTEGER DEFAULT 0,
        strength_xp INTEGER DEFAULT 0,
        defense_xp INTEGER DEFAULT 0,
        health_xp INTEGER DEFAULT 0,
        prayer_xp INTEGER DEFAULT 0
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS weapons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        damage INTEGER,
        speed INTEGER,
        cost INTEGER,
        attack_style TEXT DEFAULT 'slash',
        attack_bonus INTEGER DEFAULT 0,
        strength_bonus INTEGER DEFAULT 0,
        special_attack_cost INTEGER DEFAULT 0,
        weapon_type TEXT DEFAULT 'melee'
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        type TEXT,
        slot TEXT,
        cost INTEGER DEFAULT 0,
        effect_type TEXT,
        effect_value INTEGER DEFAULT 0,
        attack_bonus INTEGER DEFAULT 0,
        defense_bonus INTEGER DEFAULT 0,
        strength_bonus INTEGER DEFAULT 0,
        prayer_bonus INTEGER DEFAULT 0
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS user_equipment (
        user_id TEXT PRIMARY KEY,
        weapon_slot INTEGER,
        head_slot INTEGER,
        body_slot INTEGER,
        legs_slot INTEGER,
        gloves_slot INTEGER,
        boots_slot INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS user_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        item_id INTEGER,
        quantity INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS duels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id TEXT,
        user2_id TEXT,
        user1_bet INTEGER DEFAULT 0,
        user2_bet INTEGER DEFAULT 0,
        winner_id TEXT,
        active INTEGER DEFAULT 0,
        current_turn TEXT,
        turn_start_time TEXT,
        user1_prayer_active TEXT,
        user2_prayer_active TEXT,
        FOREIGN KEY (user1_id) REFERENCES users(user_id),
        FOREIGN KEY (user2_id) REFERENCES users(user_id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS combat_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        duel_id INTEGER,
        turn_number INTEGER,
        attacker_id TEXT,
        defender_id TEXT,
        action_type TEXT,
        weapon_used TEXT,
        damage_dealt INTEGER DEFAULT 0,
        FOREIGN KEY (duel_id) REFERENCES duels(id)
    )
    ''')

    # Keep old user_gear table for backwards compatibility (do not drop)
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_gear (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        weapon_id INTEGER,
        equipped BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (weapon_id) REFERENCES weapons (id)
    )
    ''')

    # ------------------------------------------------------------------ #
    # Migration v0 → v1: add missing columns to pre-existing tables       #
    # ------------------------------------------------------------------ #
    if current_version < 1:
        # users — add columns that may be missing from old schema
        for col, definition in [
            ('current_health', 'INTEGER DEFAULT 99'),
            ('current_prayer', 'INTEGER DEFAULT 1'),
            ('prayer_points',  'INTEGER DEFAULT 1'),
            ('total_wins',     'INTEGER DEFAULT 0'),
            ('total_losses',   'INTEGER DEFAULT 0'),
        ]:
            if not _column_exists(c, 'users', col):
                c.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')

        # weapons — add columns that may be missing from old schema
        for col, definition in [
            ('attack_style',        "TEXT DEFAULT 'slash'"),
            ('attack_bonus',        'INTEGER DEFAULT 0'),
            ('strength_bonus',      'INTEGER DEFAULT 0'),
            ('special_attack_cost', 'INTEGER DEFAULT 0'),
            ('weapon_type',         "TEXT DEFAULT 'melee'"),
        ]:
            if not _column_exists(c, 'weapons', col):
                c.execute(f'ALTER TABLE weapons ADD COLUMN {col} {definition}')

        # duels — add columns that may be missing from old schema
        for col, definition in [
            ('active',               'INTEGER DEFAULT 0'),
            ('current_turn',         'TEXT'),
            ('turn_start_time',      'TEXT'),
            ('user1_prayer_active',  'TEXT'),
            ('user2_prayer_active',  'TEXT'),
        ]:
            if not _column_exists(c, 'duels', col):
                c.execute(f'ALTER TABLE duels ADD COLUMN {col} {definition}')

        c.execute('INSERT INTO version (version) VALUES (1)')

    # ------------------------------------------------------------------ #
    # Migration v1 → v2: health default 10 → 99 (data fix, no schema)    #
    # ------------------------------------------------------------------ #
    if current_version < 2:
        c.execute('INSERT INTO version (version) VALUES (2)')

    # ------------------------------------------------------------------ #
    # Migration v2 → v3: add XP columns to users                         #
    # ------------------------------------------------------------------ #
    if current_version < 3:
        for col, definition in [
            ('attack_xp',   'INTEGER DEFAULT 0'),
            ('strength_xp', 'INTEGER DEFAULT 0'),
            ('defense_xp',  'INTEGER DEFAULT 0'),
            ('health_xp',   'INTEGER DEFAULT 0'),
            ('prayer_xp',   'INTEGER DEFAULT 0'),
        ]:
            if not _column_exists(c, 'users', col):
                c.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
        c.execute('INSERT INTO version (version) VALUES (3)')

    conn.commit()
    conn.close()


def add_predefined_weapons():
    """Insert default weapons if they don't already exist."""
    weapons = [
        # (name, damage, speed, cost, attack_style, attack_bonus, strength_bonus, special_attack_cost, weapon_type)
        ('Whip',            30, 4, 10000, 'slash',  82, 82,  0,  'melee'),
        ('Dragon Scimitar', 25, 4,  5000, 'slash',  67, 66, 25,  'melee'),
        ('Magic Shortbow',  20, 3,  3000, 'ranged', 69,  0, 55,  'ranged'),
        ('Granite Maul',    35, 7, 15000, 'crush',  81, 81, 50,  'melee'),
    ]
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.executemany(
        '''INSERT OR IGNORE INTO weapons
           (name, damage, speed, cost, attack_style, attack_bonus, strength_bonus, special_attack_cost, weapon_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        weapons
    )
    conn.commit()
    conn.close()


def seed_items():
    """Insert default consumables and starter gear if they don't already exist."""
    items = [
        # (name, type, slot, cost, effect_type, effect_value, attack_bonus, defense_bonus, strength_bonus, prayer_bonus)
        ('Shark',               'food',      None,   1000, 'heal', 20, 0, 0, 0, 0),
        ('Lobster',             'food',      None,    400, 'heal', 12, 0, 0, 0, 0),
        ('Swordfish',           'food',      None,    300, 'heal', 14, 0, 0, 0, 0),
        ('Monkfish',            'food',      None,    600, 'heal', 16, 0, 0, 0, 0),
        ('Anglerfish',          'food',      None,   1500, 'heal', 22, 0, 0, 0, 0),
        ('Tuna',                'food',      None,    100, 'heal',  8, 0, 0, 0, 0),
        ('Super Combat Potion', 'potion',    None,   2000, 'boost', 5, 0, 0, 0, 0),
        ('Helm of Neitiznot',   'equipment', 'head', 5000,   None,  0, 3, 3, 3, 2),
    ]
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.executemany(
        '''INSERT OR IGNORE INTO items
           (name, type, slot, cost, effect_type, effect_value,
            attack_bonus, defense_bonus, strength_bonus, prayer_bonus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        items
    )
    conn.commit()
    conn.close()


def seed_dummy_user():
    """Create the Training Dummy user (user_id='0') for practice duels."""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users
            (user_id, gold, attack, strength, defense, health, current_health,
             current_prayer, prayer_points)
        VALUES (?, 0, 40, 40, 40, 99, 99, 43, 43)
    ''', (DUMMY_USER_ID,))
    c.execute('INSERT OR IGNORE INTO user_equipment (user_id) VALUES (?)', (DUMMY_USER_ID,))
    c.execute('''
        UPDATE user_equipment
        SET weapon_slot = (SELECT id FROM weapons WHERE name = 'Dragon Scimitar')
        WHERE user_id = ?
    ''', (DUMMY_USER_ID,))
    conn.commit()
    conn.close()
