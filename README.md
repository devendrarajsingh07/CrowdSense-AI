# CrowdSense AI

AI-Powered Crowd Monitoring & Analytics Platform

## Overview

Developed and deployed an AI-powered crowd monitoring platform using YOLOv8, FastAPI, and JavaScript. Real-time analytics dashboard and reporting system were successfully deployed on Vercel and Render. Video inference requires higher-memory cloud infrastructure due to model resource requirements.

## Features

- Real-Time Person Detection
- Crowd Counting
- Risk Classification
- Occupancy Monitoring
- Alert System
- Historical Analytics
- SQLite Database
- Video Upload Analyzer
- PDF Report Generation
- Interactive Dashboard

## Technology Stack

### Backend
- Python
- FastAPI
- OpenCV
- YOLOv8
- SQLite

### Frontend
- HTML
- CSS
- JavaScript
- Chart.js

## Run Locally

Create a virtual environment and install the dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the API and dashboard:

```powershell
python -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000/dashboard/`. In a second terminal, start the camera detector:

```powershell
python detector.py
```

The database and its schema are created automatically. Press Escape in the detector window to stop it cleanly.

## Configuration

- `CROWDSENSE_MAX_UPLOAD_MB` controls the video upload limit and defaults to `100`.
- `CROWDSENSE_ALLOWED_ORIGINS` accepts a comma-separated list of frontend origins. It defaults to same/public access with no credentialed CORS requests.
- When the frontend is hosted separately, set the `crowdsense-api-base` meta tag in `frontend/index.html` to the API origin. The bundled `/dashboard/` uses same-origin requests.

Run the core unit tests with:

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Future Enhancements

- Multi-Camera Support
- Heatmaps
- Email Alerts
- Cloud Deployment

## Author

Devendra Raj Singh
