from backend.paths import MODEL_PATH


FRAME_SKIP = 15
HIGH_RISK_THRESHOLD = 8

model = None


def _dependencies():
    import cv2
    from ultralytics import YOLO

    return cv2, YOLO


def _model():
    global model
    if model is None:
        _cv2, yolo = _dependencies()
        model = yolo(str(MODEL_PATH))
    return model


def analyze_video(video_path):
    cv2, _yolo = _dependencies()
    detector = _model()
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        cap.release()
        return {"success": False, "error": "Unable to open video file"}

    max_people = 0
    total_people = 0
    sampled_frames = 0
    decoded_frames = 0
    failed_frames = 0
    high_risk_events = 0
    was_high_risk = False

    try:
        while True:
            success, frame = cap.read()

            if not success:
                break

            decoded_frames += 1

            # Always process the first frame, including for very short videos.
            if (decoded_frames - 1) % FRAME_SKIP != 0:
                continue

            try:
                results = detector(
                    frame,
                    verbose=False,
                    imgsz=256,
                    conf=0.4,
                )

                people_count = sum(
                    1
                    for result in results
                    for box in result.boxes
                    if int(box.cls[0]) == 0
                )

                max_people = max(max_people, people_count)
                total_people += people_count
                sampled_frames += 1

                is_high_risk = people_count >= HIGH_RISK_THRESHOLD
                if is_high_risk and not was_high_risk:
                    high_risk_events += 1
                was_high_risk = is_high_risk
            except Exception:
                failed_frames += 1
    finally:
        cap.release()

    if decoded_frames == 0:
        return {"success": False, "error": "The video contains no readable frames"}

    if sampled_frames == 0:
        return {
            "success": False,
            "error": "Every sampled frame failed during analysis",
        }

    return {
        "success": True,
        "max_people": max_people,
        "average_people": round(total_people / sampled_frames, 2),
        "high_risk_events": high_risk_events,
        "sampled_frames": sampled_frames,
        "failed_frames": failed_frames,
    }
