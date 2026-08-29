import csv
from pathlib import Path

from backend.paths import HISTORY_PATH


def get_analytics(history_path=HISTORY_PATH):
    history_path = Path(history_path)
    people_values = []

    if history_path.exists():
        with history_path.open("r", newline="", encoding="utf-8") as history_file:
            reader = csv.DictReader(history_file)
            for row in reader:
                try:
                    people_values.append(int(row["People"]))
                except (KeyError, TypeError, ValueError):
                    continue

    if not people_values:
        return {"peak": 0, "average": 0, "records": 0}

    return {
        "peak": max(people_values),
        "average": round(sum(people_values) / len(people_values), 2),
        "records": len(people_values),
    }
