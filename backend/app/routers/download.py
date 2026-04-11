"""Download router — serve generated SRT, dubbed audio and dubbed video files."""
import logging
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["download"])


@router.get("/download/{filename}")
async def download_srt(filename: str):
    """
    Download a generated SRT file.

    Args:
        filename: Name of the SRT file to download.

    Returns:
        FileResponse with the SRT file.
    """
    # Sanitize filename — prevent directory traversal
    safe_name = os.path.basename(filename)
    file_path = os.path.join(settings.OUTPUT_DIR, safe_name)

    logger.info(f"SRT download requested: filename={filename!r}, safe_name={safe_name!r}, file_path={file_path!r}")
    logger.info(f"OUTPUT_DIR={settings.OUTPUT_DIR}, file exists={os.path.isfile(file_path)}")

    if not os.path.isfile(file_path):
        logger.warning(f"SRT file not found: {file_path}")
        # List available files for debugging
        if os.path.isdir(settings.OUTPUT_DIR):
            available = os.listdir(settings.OUTPUT_DIR)
            logger.info(f"Available files in OUTPUT_DIR: {available}")
        else:
            logger.warning(f"OUTPUT_DIR does not exist: {settings.OUTPUT_DIR}")
        raise HTTPException(status_code=404, detail=f"Fichier '{safe_name}' non trouvé.")

    try:
        return FileResponse(
            path=file_path,
            media_type="text/plain",
            filename=safe_name,
        )
    except Exception as e:
        logger.error(f"Error serving SRT file {file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement : {e}")


@router.get("/srt-preview/{filename}")
async def preview_srt(filename: str):
    """
    Preview the content of a generated SRT file.

    Returns:
        JSON with the SRT file content.
    """
    safe_name = os.path.basename(filename)
    file_path = os.path.join(settings.OUTPUT_DIR, safe_name)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"Fichier '{safe_name}' non trouvé.")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "filename": safe_name,
        "content": content,
    }


@router.get("/download-dubbed-video/{filename}")
async def download_dubbed_video(filename: str):
    """
    Download a dubbed video file (video with replaced French audio).

    Args:
        filename: Name of the dubbed video file.

    Returns:
        FileResponse with the dubbed video file.
    """
    safe_name = os.path.basename(filename)
    file_path = os.path.join(settings.OUTPUT_DIR, safe_name)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"Fichier '{safe_name}' non trouvé.")

    # Determine media type based on extension
    ext = os.path.splitext(safe_name)[1].lower()
    media_types = {
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
    }
    media_type = media_types.get(ext, "video/mp4")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=safe_name,
    )


@router.get("/download-dubbed-audio/{filename}")
async def download_dubbed_audio(filename: str):
    """
    Download the dubbed audio track (French voice only).

    Args:
        filename: Name of the dubbed audio file.

    Returns:
        FileResponse with the dubbed audio WAV file.
    """
    safe_name = os.path.basename(filename)
    file_path = os.path.join(settings.OUTPUT_DIR, safe_name)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"Fichier '{safe_name}' non trouvé.")

    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=safe_name,
    )
