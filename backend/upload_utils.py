from pathlib import Path
from uuid import uuid4


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def validated_video_suffix(filename):
    normalized_name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    suffix = Path(normalized_name).suffix.lower()

    if not normalized_name or suffix not in ALLOWED_VIDEO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_VIDEO_EXTENSIONS))
        raise ValueError(f"Unsupported video type. Allowed extensions: {allowed}")

    return suffix


def allocate_upload_path(upload_directory, filename):
    upload_directory = Path(upload_directory).resolve()
    suffix = validated_video_suffix(filename)
    return upload_directory / f"{uuid4().hex}{suffix}"
