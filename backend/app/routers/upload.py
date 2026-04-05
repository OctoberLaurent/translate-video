"""Upload router — handle video file uploads."""
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