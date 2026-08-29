import sqlite3
from contextlib import closing
from pathlib import Path

from backend.paths import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS crowd_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    people_count INTEGER NOT NULL,
    risk TEXT NOT NULL,
    confidence REAL NOT NULL,
    occupancy REAL NOT NULL
)
"""

def initialize_database(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(db_path, timeout=5)) as conn:
        with conn:
            conn.execute(SCHEMA)

def insert_record(
    timestamp,
    people_count,
    risk,
    confidence,
    occupancy,
    db_path=DB_PATH,
):
    initialize_database(db_path)

    with closing(sqlite3.connect(db_path, timeout=5)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO crowd_logs
                (timestamp, people_count, risk, confidence, occupancy)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, people_count, risk, confidence, occupancy),
            )
