"""Models router — list available Whisper and LM Studio models."""
from fastapi import APIRouter, HTTPException

from app.utils.config import settings
from app.services.translator import TranslatorService

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/whisper-models")
async def get_whisper_models():
    """
    Return available Whisper model sizes.
    
    Returns:
        JSON with the list of available model sizes and recommended default.
    """
    return {
        "models": settings.WHISPER_MODELS,
        "default": settings.WHISPER_DEFAULT_MODEL,
    }


@router.get("/llm-models")
async def get_llm_models(port: int | None = None):
    """
    Fetch and return models currently loaded in LM Studio.
    
    Args:
        port: LM Studio server port (default: 1234).
    
    Returns:
        JSON with the list of available LLM models from LM Studio.
    """
    try:
        translator = TranslatorService(port=port)
        models = await translator.get_available_models()
        return {
            "models": models,
            "connected": True,
        }
    except ConnectionError as e:
        return {
            "models": [],
            "connected": False,
            "error": str(e),
        }


@router.get("/device")
async def get_device_info():
    """
    Return detected compute device information.
    
    Returns:
        JSON with device type and platform info.
    """
    import platform
    
    device = settings.detect_device()
    
    return {
        "device": device,
        "platform": platform.system(),
        "machine": platform.machine(),
    }