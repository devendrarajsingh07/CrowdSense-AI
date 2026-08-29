import sqlite3
from contextlib import closing

from backend.database import initialize_database
from backend.paths import DB_PATH


initialize_database()

with closing(sqlite3.connect(DB_PATH)) as conn:
    rows = conn.execute("SELECT * FROM crowd_logs LIMIT 10").fetchall()

for row in rows:
    print(row)
