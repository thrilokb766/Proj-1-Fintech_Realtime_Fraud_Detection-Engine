"""
SentinelStream - Database Layer
SQLite database initialization and connection management
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sentinelstream.db")


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            description TEXT,
            status TEXT NOT NULL,          -- 'Safe' or 'Fraud'
            risk_level TEXT NOT NULL,      -- 'Low', 'Medium', 'High', 'Critical'
            risk_score REAL NOT NULL,
            flagged_reason TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully.")
