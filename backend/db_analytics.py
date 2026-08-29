import sqlite3
from contextlib import closing
from pathlib import Path

from backend.database import initialize_database
from backend.paths import DB_PATH


def get_database_analytics(db_path=DB_PATH):
    db_path = Path(db_path)
    initialize_database(db_path)

    with closing(sqlite3.connect(db_path, timeout=5)) as conn:
        total_records = conn.execute("SELECT COUNT(*) FROM crowd_logs").fetchone()[0]
        high_risk_events = conn.execute(
            "SELECT COUNT(*) FROM crowd_logs WHERE risk = 'HIGH'"
        ).fetchone()[0]
        avg_occupancy = conn.execute(
            "SELECT AVG(occupancy) FROM crowd_logs"
        ).fetchone()[0]

    return {
        "db_records": total_records,
        "high_risk": high_risk_events,
        "avg_occupancy": round(avg_occupancy or 0, 2),
    }
