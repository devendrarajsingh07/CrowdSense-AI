import logging
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
STATE_WRITE_INTERVAL_SECONDS = 0.5
MAX_CONSECUTIVE_READ_FAILURES = 30

logger = logging.getLogger(__name__)


def _safe_write_state(state, camera="ONLINE"):
    """A failed state write must not stop the detector."""
    try:
        write_crowd_state(state, camera=camera)
    except OSError:
        logger.warning("Could not write crowd state", exc_info=True)


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
    last_log_time = float("-inf")
    last_state_write = float("-inf")
    consecutive_read_failures = 0

    if not cap.isOpened():
        cap.release()
        _safe_write_state(DEFAULT_STATE, camera="OFFLINE")
        raise RuntimeError(f"Unable to open camera {camera_index}")

    try:
        while True:
            success, frame = cap.read()

            if not success:
                # Webcams occasionally drop a frame; only stop on a real outage.
                consecutive_read_failures += 1
                if consecutive_read_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                    logger.error("Camera stopped returning frames")
                    break
                time.sleep(0.05)
                continue

            consecutive_read_failures = 0

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
            current_time = time.monotonic()

            # The dashboard polls every 2 s; writing every frame only adds
            # disk churn (and file-lock collisions on Windows/OneDrive).
            if current_time - last_state_write >= STATE_WRITE_INTERVAL_SECONDS:
                _safe_write_state(state)
                last_state_write = current_time

            if current_time - last_log_time >= LOG_INTERVAL_SECONDS:
                timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
                try:
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
                except Exception:
                    logger.warning("Could not log crowd history", exc_info=True)
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
        _safe_write_state(DEFAULT_STATE, camera="OFFLINE")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_detector()
