import sqlite3


def get_db_connection():
    conn = sqlite3.connect('duelbot.db')
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    conn = get_db_connection()
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
    c = conn.cursor()
    c.executemany('INSERT OR IGNORE INTO weapons (name, damage, speed, cost) VALUES (?, ?, ?, ?)', weapons)
    conn.commit()
    conn.close()
