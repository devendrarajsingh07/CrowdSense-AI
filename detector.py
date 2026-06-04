import cv2
import json
import csv
import time

from datetime import datetime
from ultralytics import YOLO

from backend.database import insert_record

# Load YOLO Model
model = YOLO("yolov8n.pt")

# Maximum Capacity
MAX_CAPACITY = 20

# Log every 5 seconds
last_log_time = 0

# Webcam
cap = cv2.VideoCapture(0)

while True:

    success, frame = cap.read()

    if not success:
        break

    results = model(frame, verbose=False)

    people_count = 0
    confidence_sum = 0

    for result in results:

        for box in result.boxes:

            cls = int(box.cls[0])

            if cls == 0:

                people_count += 1

                confidence = float(box.conf[0])

                confidence_sum += confidence

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"{confidence:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

    # Average Confidence

    if people_count > 0:

        avg_confidence = round(
            (confidence_sum / people_count) * 100,
            2
        )

    else:

        avg_confidence = 0

    # Risk Level

    if people_count < 3:

        level = "LOW"

    elif people_count < 8:

        level = "MEDIUM"

    else:

        level = "HIGH"

    # Occupancy %

    occupancy = round(
        (people_count / MAX_CAPACITY) * 100,
        2
    )

    # Alert

    if people_count >= 8:

        alert = "HIGH CROWD DETECTED"

    else:

        alert = "No Alert"

    # Dashboard JSON

    data = {

        "people": people_count,
        "risk": level,
        "confidence": avg_confidence,
        "occupancy": occupancy,
        "alert": alert

    }

    with open(
        "crowd_data.json",
        "w"
    ) as file:

        json.dump(
            data,
            file
        )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Log every 5 seconds

    current_time = time.time()

    if current_time - last_log_time >= 5:

        # CSV Logging

        with open(
            "data/crowd_history.csv",
            "a",
            newline=""
        ) as csvfile:

            writer = csv.writer(
                csvfile
            )

            writer.writerow([
                timestamp,
                people_count,
                level,
                avg_confidence,
                occupancy
            ])

        # SQLite Logging

        insert_record(
            timestamp,
            people_count,
            level,
            avg_confidence,
            occupancy
        )

        last_log_time = current_time

    # Display Information

    cv2.putText(
        frame,
        f"People: {people_count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Risk: {level}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Confidence: {avg_confidence}%",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Occupancy: {occupancy}%",
        (20, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 0, 255),
        2
    )

    if alert == "HIGH CROWD DETECTED":

        cv2.putText(
            frame,
            alert,
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "CrowdSense AI",
        frame
    )

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()