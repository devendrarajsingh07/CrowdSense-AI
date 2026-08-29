import csv
from pathlib import Path

from backend.paths import HISTORY_PATH


HISTORY_FIELDS = ["Timestamp", "People", "Risk", "Confidence", "Occupancy"]


def append_history_record(
    timestamp,
    people_count,
    risk,
    confidence,
    occupancy,
    path=HISTORY_PATH,
):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path.exists() or path.stat().st_size == 0

    with path.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        if needs_header:
            writer.writerow(HISTORY_FIELDS)
        writer.writerow([timestamp, people_count, risk, confidence, occupancy])
