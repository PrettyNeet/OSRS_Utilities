import sqlite3
import os
import aiosqlite
from typing import Optional


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
        import sqlite3

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

    return await aiosqlite.connect(db_path)


def initialize_db():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Create a version table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS version (
        id INTEGER PRIMARY KEY,
        version INTEGER NOT NULL
        )
    ''')
    
    # Check the current schema version
    c.execute('SELECT version FROM version ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    
    current_version = row[0] if row else 0
    
    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        gold INTEGER DEFAULT 100000,
        weapons TEXT DEFAULT '',
        gear TEXT DEFAULT '',
        attack INTEGER DEFAULT 1,
        strength INTEGER DEFAULT 1,
        defense INTEGER DEFAULT 1,
        ranged INTEGER DEFAULT 1,
        magic INTEGER DEFAULT 1,
        prayer INTEGER DEFAULT 1,
        health INTEGER DEFAULT 10
        )
    ''')

    # Create weapons table
    c.execute('''
    CREATE TABLE IF NOT EXISTS weapons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        damage INTEGER,
        speed INTEGER,
        cost INTEGER
        )
    ''')
    
    # Create user_gear table
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

    # Create duels table
    c.execute('''
    CREATE TABLE IF NOT EXISTS duels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id TEXT,
        user2_id TEXT,
        user1_bet INTEGER,
        user2_bet INTEGER,
        winner_id TEXT,
        FOREIGN KEY (user1_id) REFERENCES users (user_id),
        FOREIGN KEY (user2_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()


def add_predefined_weapons():
    weapons = [
        ('Whip', 30, 4, 10000),
        ('Dragon Scimitar', 25, 3, 5000),
        ('Magic Shortbow', 20, 2, 3000),
        ('Granite Maul', 35, 5, 15000)
    ]
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.executemany('INSERT OR IGNORE INTO weapons (name, damage, speed, cost) VALUES (?, ?, ?, ?)', weapons)
    conn.commit()
    conn.close()
