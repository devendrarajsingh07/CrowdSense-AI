import sqlite3

def get_database_analytics():

    try:

        conn = sqlite3.connect(
            "crowd.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM crowd_logs
            """
        )

        total_records = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM crowd_logs
            WHERE risk='HIGH'
            """
        )

        high_risk_events = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT AVG(occupancy)
            FROM crowd_logs
            """
        )

        avg_occupancy = cursor.fetchone()[0]

        if avg_occupancy is None:
            avg_occupancy = 0

        conn.close()

        return {

            "db_records":
            total_records,

            "high_risk":
            high_risk_events,

            "avg_occupancy":
            round(avg_occupancy,2)

        }

    except:

        return {

            "db_records":0,
            "high_risk":0,
            "avg_occupancy":0

        }