import time
from datetime import datetime

import cv2
from ultralytics import YOLO

from backend.database import initialize_database, insert_record
from backend.history import append_history_record
from backend.paths import MODEL_PATH
from backend.state import DEFAULT_STATE, write_crowd_state


MAX_CAPACITY = 20
HIGH_RISK_THRESHOLD = 8
LOG_INTERVAL_SECONDS = 5


def _crowd_state(people_count, confidence_sum):
    if people_count:
        average_confidence = round((confidence_sum / people_count) * 100, 2)
    else:
        average_confidence = 0

    if people_count < 3:
        risk = "LOW"
    elif people_count < HIGH_RISK_THRESHOLD:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    occupancy = min(round((people_count / MAX_CAPACITY) * 100, 2), 100)
    alert = "HIGH CROWD DETECTED" if risk == "HIGH" else "No Alert"

    return {
        "people": people_count,
        "risk": risk,
        "confidence": average_confidence,
        "occupancy": occupancy,
        "alert": alert,
    }


def run_detector(camera_index=0):
    initialize_database()
    model = YOLO(str(MODEL_PATH))
    cap = cv2.VideoCapture(camera_index)
    last_log_time = 0

    if not cap.isOpened():
        write_crowd_state(DEFAULT_STATE, camera="OFFLINE")
        raise RuntimeError(f"Unable to open camera {camera_index}")

    try:
        while True:
            success, frame = cap.read()

            if not success:
                break

            results = model(frame, verbose=False)
            people_count = 0
            confidence_sum = 0

            for result in results:
                for box in result.boxes:
                    if int(box.cls[0]) != 0:
                        continue

                    people_count += 1
                    confidence = float(box.conf[0])
                    confidence_sum += confidence
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{confidence:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

            state = _crowd_state(people_count, confidence_sum)
            write_crowd_state(state)

            current_time = time.monotonic()
            if current_time - last_log_time >= LOG_INTERVAL_SECONDS:
                timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
                append_history_record(
                    timestamp,
                    state["people"],
                    state["risk"],
                    state["confidence"],
                    state["occupancy"],
                )
                insert_record(
                    timestamp,
                    state["people"],
                    state["risk"],
                    state["confidence"],
                    state["occupancy"],
                )
                last_log_time = current_time

            cv2.putText(
                frame,
                f"People: {state['people']}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Risk: {state['risk']}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"Confidence: {state['confidence']}%",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Occupancy: {state['occupancy']}%",
                (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 0, 255),
                2,
            )

            if state["alert"] == "HIGH CROWD DETECTED":
                cv2.putText(
                    frame,
                    state["alert"],
                    (20, 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )

            cv2.imshow("CrowdSense AI", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        write_crowd_state(DEFAULT_STATE, camera="OFFLINE")


if __name__ == "__main__":
    run_detector()
