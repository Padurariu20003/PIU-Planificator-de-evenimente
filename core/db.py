import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "eventease.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]
    if column not in cols:
        cur.execute(ddl)
        conn.commit()

def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'user'))
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS halls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            layout_json TEXT NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            hall_id INTEGER NOT NULL,
            FOREIGN KEY (hall_id) REFERENCES halls(id) ON DELETE CASCADE
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            seats_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            total_price REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        );
        """
    )

    _ensure_column(
        conn,
        "bookings",
        "total_price",
        "ALTER TABLE bookings ADD COLUMN total_price REAL NOT NULL DEFAULT 0;",
    )


    conn.commit()
    conn.close()
