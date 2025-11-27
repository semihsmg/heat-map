import sqlite3
import os
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path


def get_db_path() -> Path:
    """Get the database path in AppData folder."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    db_dir = Path(appdata) / 'KeyboardHeatMap'
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / 'keystrokes.db'


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keystrokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_timestamp ON keystrokes(timestamp)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_key ON keystrokes(key)
    ''')

    conn.commit()
    conn.close()


def log_key(key: str):
    """Log a single key press to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO keystrokes (key, timestamp) VALUES (?, ?)',
        (key, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_key_counts(period: str = 'all') -> Counter:
    """
    Get key press counts for a given time period.

    Args:
        period: 'today', 'week', 'month', or 'all'

    Returns:
        Counter object with key counts
    """
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()

    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute(
            'SELECT key, COUNT(*) as count FROM keystrokes WHERE timestamp >= ? GROUP BY key',
            (start.isoformat(),)
        )
    elif period == 'week':
        # Week starts on Monday
        days_since_monday = now.weekday()
        start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute(
            'SELECT key, COUNT(*) as count FROM keystrokes WHERE timestamp >= ? GROUP BY key',
            (start.isoformat(),)
        )
    elif period == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cursor.execute(
            'SELECT key, COUNT(*) as count FROM keystrokes WHERE timestamp >= ? GROUP BY key',
            (start.isoformat(),)
        )
    else:  # all
        cursor.execute('SELECT key, COUNT(*) as count FROM keystrokes GROUP BY key')

    counts = Counter()
    for row in cursor.fetchall():
        counts[row['key']] = row['count']

    conn.close()
    return counts


def get_total_keystrokes(period: str = 'all') -> int:
    """Get total keystroke count for a given time period."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()

    if period == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute('SELECT COUNT(*) FROM keystrokes WHERE timestamp >= ?', (start.isoformat(),))
    elif period == 'week':
        days_since_monday = now.weekday()
        start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute('SELECT COUNT(*) FROM keystrokes WHERE timestamp >= ?', (start.isoformat(),))
    elif period == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cursor.execute('SELECT COUNT(*) FROM keystrokes WHERE timestamp >= ?', (start.isoformat(),))
    else:
        cursor.execute('SELECT COUNT(*) FROM keystrokes')

    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_today_count() -> int:
    """Quick helper to get today's keystroke count for tooltip."""
    return get_total_keystrokes('today')
