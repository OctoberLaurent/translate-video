"""Download router — serve generated SRT files."""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.utils.config import settings

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

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"Fichier '{safe_name}' non trouvé.")

    return FileResponse(
        path=file_path,
        media_type="text/plain",
        filename=safe_name,
        headers={
            "Content-Disposition": f"attachment; filename={safe_name}",
        },
    )


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