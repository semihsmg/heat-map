import sqlite3
import os
from datetime import datetime, timedelta, date
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
        CREATE TABLE IF NOT EXISTS daily_counts (
            key TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (key, date)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_date ON daily_counts(date)
    ''')

    conn.commit()
    conn.close()


def flush_counts(counts: Counter):
    """
    Flush buffered key counts to the database.
    Uses UPSERT to increment existing counts or insert new rows.
    """
    if not counts:
        return

    today = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()

    for key, count in counts.items():
        cursor.execute('''
            INSERT INTO daily_counts (key, date, count)
            VALUES (?, ?, ?)
            ON CONFLICT(key, date) DO UPDATE SET count = count + excluded.count
        ''', (key, today, count))

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

    today = date.today()

    if period == 'today':
        cursor.execute(
            'SELECT key, SUM(count) as total FROM daily_counts WHERE date = ? GROUP BY key',
            (today.isoformat(),)
        )
    elif period == 'week':
        # Week starts on Monday
        days_since_monday = today.weekday()
        start = today - timedelta(days=days_since_monday)
        cursor.execute(
            'SELECT key, SUM(count) as total FROM daily_counts WHERE date >= ? GROUP BY key',
            (start.isoformat(),)
        )
    elif period == 'month':
        start = today.replace(day=1)
        cursor.execute(
            'SELECT key, SUM(count) as total FROM daily_counts WHERE date >= ? GROUP BY key',
            (start.isoformat(),)
        )
    else:  # all
        cursor.execute('SELECT key, SUM(count) as total FROM daily_counts GROUP BY key')

    counts = Counter()
    for row in cursor.fetchall():
        counts[row['key']] = row['total']

    conn.close()
    return counts


def get_total_keystrokes(period: str = 'all') -> int:
    """Get total keystroke count for a given time period."""
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today()

    if period == 'today':
        cursor.execute(
            'SELECT SUM(count) FROM daily_counts WHERE date = ?',
            (today.isoformat(),)
        )
    elif period == 'week':
        days_since_monday = today.weekday()
        start = today - timedelta(days=days_since_monday)
        cursor.execute(
            'SELECT SUM(count) FROM daily_counts WHERE date >= ?',
            (start.isoformat(),)
        )
    elif period == 'month':
        start = today.replace(day=1)
        cursor.execute(
            'SELECT SUM(count) FROM daily_counts WHERE date >= ?',
            (start.isoformat(),)
        )
    else:
        cursor.execute('SELECT SUM(count) FROM daily_counts')

    result = cursor.fetchone()[0]
    conn.close()
    return result or 0


def get_today_count() -> int:
    """Quick helper to get today's keystroke count for tooltip."""
    return get_total_keystrokes('today')
