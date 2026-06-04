import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "crowd.db"
)

def initialize_database():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crowd_logs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        timestamp TEXT,

        people_count INTEGER,

        risk TEXT,

        confidence REAL,

        occupancy REAL

    )
    """)

    conn.commit()
    conn.close()

def insert_record(
    timestamp,
    people_count,
    risk,
    confidence,
    occupancy
):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO crowd_logs
        (
            timestamp,
            people_count,
            risk,
            confidence,
            occupancy
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            people_count,
            risk,
            confidence,
            occupancy
        )
    )

    conn.commit()
    conn.close()