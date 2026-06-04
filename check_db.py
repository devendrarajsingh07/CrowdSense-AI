import sqlite3

conn = sqlite3.connect("crowd.db")

cursor = conn.cursor()

cursor.execute(
    "SELECT * FROM crowd_logs LIMIT 10"
)

rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()