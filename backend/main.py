from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from fastapi.responses import FileResponse

from backend.analytics import get_analytics
from backend.db_analytics import get_database_analytics
from backend.video_analyzer import analyze_video
from backend.report_generator import generate_report

import json
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/crowd")
def get_crowd_data():

    try:

        with open(
            "crowd_data.json",
            "r"
        ) as file:

            data = json.load(file)

        analytics = get_analytics()

        db_stats = get_database_analytics()

        data.update(analytics)
        data.update(db_stats)

        return data

    except Exception as e:

        return {

            "people": 0,
            "risk": "LOW",
            "confidence": 0,
            "occupancy": 0,
            "alert": "No Alert",

            "peak": 0,
            "average": 0,
            "records": 0,

            "db_records": 0,
            "high_risk": 0,
            "avg_occupancy": 0,

            "error": str(e)

        }

@app.post("/analyze-video")
async def analyze_uploaded_video(
    file: UploadFile = File(...)
):

    file_path = (
        "uploads/" +
        file.filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    result = analyze_video(
        file_path
    )

    return result

@app.get("/generate-report")
def create_report():

    with open(
        "crowd_data.json",
        "r"
    ) as file:

        data = json.load(file)

    analytics = get_analytics()
    db_stats = get_database_analytics()

    data.update(analytics)
    data.update(db_stats)

    filename = generate_report(data)

    return FileResponse(
        filename,
        media_type="application/pdf",
        filename=filename
    )