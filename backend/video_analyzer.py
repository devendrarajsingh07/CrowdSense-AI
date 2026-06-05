import os
import cv2
from ultralytics import YOLO

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "yolov8n.pt"
)

model = YOLO(MODEL_PATH)

def analyze_video(video_path):

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():

        return {
            "error": "Unable to open video file"
        }

    max_people = 0
    total_people = 0
    frame_count = 0
    high_risk_events = 0

    frame_skip = 15
    current_frame = 0

    while True:

        success, frame = cap.read()

        if not success:
            break

        current_frame += 1

        if current_frame % frame_skip != 0:
            continue

        try:

            results = model(
                frame,
                verbose=False,
                imgsz=256,
                conf=0.4
            )

            people_count = 0

            for result in results:

                for box in result.boxes:

                    if int(box.cls[0]) == 0:
                        people_count += 1

            max_people = max(
                max_people,
                people_count
            )

            total_people += people_count

            frame_count += 1

            if people_count >= 8:
                high_risk_events += 1

        except Exception as e:

            print("Frame processing error:", e)

    cap.release()

    average_people = 0

    if frame_count > 0:

        average_people = round(
            total_people / frame_count,
            2
        )

    return {

        "success": True,
        "max_people": max_people,
        "average_people": average_people,
        "high_risk_events": high_risk_events

    }