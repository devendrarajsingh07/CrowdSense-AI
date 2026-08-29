import csv
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.analytics import get_analytics
from backend.database import insert_record
from backend.state import read_crowd_state, write_crowd_state
from backend.upload_utils import allocate_upload_path, validated_video_suffix


class DatabaseTests(unittest.TestCase):
    def test_insert_initializes_a_fresh_database(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "nested" / "crowd.db"
            insert_record("2026-01-01T00:00:00Z", 2, "LOW", 90, 10, db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                record = connection.execute(
                    "SELECT people_count, risk FROM crowd_logs"
                ).fetchone()

            self.assertEqual(record, (2, "LOW"))


class StateTests(unittest.TestCase):
    def test_atomic_state_round_trip_is_online(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            write_crowd_state(
                {
                    "people": 3,
                    "risk": "MEDIUM",
                    "confidence": 88.5,
                    "occupancy": 15,
                    "alert": "No Alert",
                },
                state_path,
            )

            state = read_crowd_state(state_path, max_age_seconds=10)

            self.assertEqual(state["camera"], "ONLINE")
            self.assertEqual(state["people"], 3)

    def test_stale_state_is_reported_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            stale_time = datetime.now(timezone.utc) - timedelta(minutes=1)
            state_path.write_text(
                json.dumps(
                    {
                        "people": 50,
                        "risk": "HIGH",
                        "confidence": 99,
                        "occupancy": 100,
                        "alert": "HIGH CROWD DETECTED",
                        "camera": "ONLINE",
                        "updated_at": stale_time.isoformat(),
                    }
                ),
                encoding="utf-8",
            )

            state = read_crowd_state(state_path, max_age_seconds=10)

            self.assertEqual(state["camera"], "OFFLINE")
            self.assertEqual(state["people"], 0)

    def test_invalid_numeric_state_is_reported_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "people": "not-a-number",
                        "camera": "ONLINE",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                encoding="utf-8",
            )

            state = read_crowd_state(state_path)

            self.assertEqual(state["camera"], "OFFLINE")


class AnalyticsTests(unittest.TestCase):
    def test_invalid_rows_are_skipped_without_losing_valid_data(self):
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "history.csv"
            with history_path.open("w", newline="", encoding="utf-8") as history:
                writer = csv.writer(history)
                writer.writerow(["Timestamp", "People", "Risk", "Confidence", "Occupancy"])
                writer.writerow(["one", "2", "LOW", "90", "10"])
                writer.writerow(["two", "invalid", "LOW", "90", "10"])
                writer.writerow(["three", "6", "MEDIUM", "90", "30"])

            self.assertEqual(
                get_analytics(history_path),
                {"peak": 6, "average": 4.0, "records": 2},
            )


class UploadTests(unittest.TestCase):
    def test_path_traversal_filename_is_replaced_with_uuid(self):
        with tempfile.TemporaryDirectory() as directory:
            upload_directory = Path(directory) / "uploads"
            path = allocate_upload_path(upload_directory, "../../crowd_data.mp4")

            self.assertEqual(path.parent, upload_directory.resolve())
            self.assertNotIn("crowd_data", path.name)
            self.assertEqual(path.suffix, ".mp4")

    def test_unsupported_extension_is_rejected(self):
        with self.assertRaises(ValueError):
            validated_video_suffix("payload.py")


if __name__ == "__main__":
    unittest.main()
