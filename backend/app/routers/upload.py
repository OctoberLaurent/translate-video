"""Upload router — handle video and SRT file uploads."""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.utils.config import settings

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file for processing.

    Accepts common video formats: MP4, MKV, AVI, MOV, WMV, FLV, WEBM.

    Returns:
        JSON with the upload ID and file information.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté '{ext}'. "
            f"Formats acceptés : {', '.join(settings.SUPPORTED_EXTENSIONS)}",
        )

    # Generate unique ID and save file
    upload_id = str(uuid.uuid4())[:8]
    safe_name = f"{upload_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    # Write the file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_size_mb = len(content) / (1024 * 1024)

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "file_path": file_path,
        "file_size_mb": round(file_size_mb, 2),
        "extension": ext,
    }


@router.post("/upload-srt")
async def upload_srt(file: UploadFile = File(...)):
    """
    Upload an SRT subtitle file for TTS dubbing.

    Accepts .srt files only.

    Returns:
        JSON with the upload ID and file information.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext != ".srt":
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté '{ext}'. Seuls les fichiers .srt sont acceptés.",
        )

    # Generate unique ID and save file
    upload_id = str(uuid.uuid4())[:8]
    safe_name = f"{upload_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Write the file
    content = await file.read()

    # Validate that it looks like an SRT file (basic check)
    try:
        text = content.decode("utf-8")
        if "-->" not in text:
            raise ValueError("No timestamps found")
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Le fichier ne semble pas être un fichier SRT valide.",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    file_size_kb = len(content) / 1024

    # Quick count of segments
    segment_count = text.count("-->")

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "file_path": file_path,
        "file_size_kb": round(file_size_kb, 2),
        "segment_count": segment_count,
    }


@router.post("/upload-video-for-tts")
async def upload_video_for_tts(file: UploadFile = File(...)):
    """
    Upload a video file for TTS dubbing (used with standalone SRT dubbing).

    Accepts common video formats.

    Returns:
        JSON with the upload ID and file information.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni.")

    ext = Path(file.filename).suffix.lower()
    video_extensions = settings.SUPPORTED_EXTENSIONS
    if ext not in video_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté '{ext}'. "
            f"Formats acceptés : {', '.join(video_extensions)}",
        )

    upload_id = str(uuid.uuid4())[:8]
    safe_name = f"{upload_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_size_mb = len(content) / (1024 * 1024)

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "file_path": file_path,
        "file_size_mb": round(file_size_mb, 2),
        "extension": ext,
    }
