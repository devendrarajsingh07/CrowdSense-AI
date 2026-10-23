import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from backend.analytics import get_analytics
from backend.database import initialize_database
from backend.db_analytics import get_database_analytics
from backend.paths import DATA_DIR, FRONTEND_DIR, UPLOAD_DIR
from backend.report_generator import generate_report
from backend.state import read_crowd_state
from backend.upload_utils import allocate_upload_path
from backend.video_analyzer import analyze_video


logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = int(os.getenv("CROWDSENSE_MAX_UPLOAD_MB", "100")) * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024
MULTIPART_OVERHEAD_BYTES = 1024 * 1024
VIDEO_SLOT_TIMEOUT_SECONDS = 0.25
video_analysis_slot = asyncio.Semaphore(1)


class UploadTooLarge(Exception):
    pass


class UploadSizeLimitMiddleware:
    """Enforce the request limit before multipart parsing, including chunked bodies."""

    def __init__(self, app, max_request_bytes):
        self.app = app
        self.max_request_bytes = max_request_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/analyze-video":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")

        if content_length:
            try:
                declared_bytes = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length"},
                )
                await response(scope, receive, send)
                return

            if declared_bytes > self.max_request_bytes:
                await self._reject(scope, receive, send)
                return

        received_bytes = 0
        limit_exceeded = False
        response_started = False

        async def limited_receive():
            nonlocal received_bytes, limit_exceeded
            message = await receive()

            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_request_bytes:
                    limit_exceeded = True
                    raise UploadTooLarge

            return message

        async def guarded_send(message):
            nonlocal response_started
            # FastAPI converts body-parsing exceptions into a generic 400.
            # Once the limit is hit, drop that response and send a 413 instead.
            if limit_exceeded:
                return
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except UploadTooLarge:
            pass

        if limit_exceeded and not response_started:
            await self._reject(scope, receive, send)

    async def _reject(self, scope, receive, send):
        response = JSONResponse(
            status_code=413,
            content={
                "detail": f"Video exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit"
            },
        )
        await response(scope, receive, send)


def _allowed_origins():
    configured = os.getenv("CROWDSENSE_ALLOWED_ORIGINS", "*")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def _delete_file(path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


async def _save_bounded_upload(upload, destination):
    bytes_written = 0

    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(UPLOAD_CHUNK_BYTES):
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Video exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
                    )
                output.write(chunk)
    finally:
        await upload.close()

    if bytes_written == 0:
        raise HTTPException(status_code=400, detail="The uploaded video is empty")


@asynccontextmanager
async def lifespan(_app):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()
    yield


app = FastAPI(lifespan=lifespan)

origins = _allowed_origins()
# Middleware added last runs first. CORS must wrap the upload limiter so that
# 413 responses still carry CORS headers and the browser can read the error.
app.add_middleware(
    UploadSizeLimitMiddleware,
    max_request_bytes=MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "CrowdSense AI API Running",
        "dashboard": "/dashboard/",
    }


@app.get("/crowd")
def get_crowd_data():
    data = read_crowd_state()
    data.update(get_analytics())
    data.update(get_database_analytics())
    return data


@app.post("/analyze-video")
async def analyze_uploaded_video(file: UploadFile = File(...)):
    try:
        destination = allocate_upload_path(UPLOAD_DIR, file.filename)
    except ValueError as error:
        await file.close()
        raise HTTPException(status_code=415, detail=str(error)) from error

    try:
        await asyncio.wait_for(
            video_analysis_slot.acquire(),
            timeout=VIDEO_SLOT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as error:
        await file.close()
        raise HTTPException(
            status_code=429,
            detail="Another video is currently being analyzed. Try again shortly.",
        ) from error

    try:
        await _save_bounded_upload(file, destination)
        result = await run_in_threadpool(analyze_video, destination)

        if not result.get("success"):
            raise HTTPException(
                status_code=422,
                detail=result.get("error", "Video analysis failed"),
            )

        return result
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Video analysis failed")
        raise HTTPException(status_code=500, detail="Video analysis failed") from error
    finally:
        _delete_file(destination)
        video_analysis_slot.release()


@app.get("/generate-report")
def create_report():
    try:
        data = read_crowd_state()
        data.update(get_analytics())
        data.update(get_database_analytics())
        filename = generate_report(data)
    except Exception as error:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=500, detail="Report generation failed") from error

    return FileResponse(
        filename,
        media_type="application/pdf",
        filename="Crowd_Report.pdf",
        background=BackgroundTask(_delete_file, filename),
    )


if FRONTEND_DIR.is_dir():
    app.mount(
        "/dashboard",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="dashboard",
    )
