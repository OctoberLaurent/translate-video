"""Configuration module for the application."""
import os
import platform
import tempfile
from pathlib import Path


class Settings:
    """Application settings with auto-detection of platform capabilities."""

    # LM Studio API
    LM_STUDIO_BASE_URL: str = "http://localhost:7890/v1"
    LM_STUDIO_TIMEOUT: int = 300  # 5 minutes timeout

    # Whisper settings
    WHISPER_MODELS: list[str] = ["base", "small", "medium", "large-v3"]
    WHISPER_DEFAULT_MODEL: str = "base"

    # Translation settings
    TRANSLATION_CHUNK_SIZE: int = 20  # Number of subtitles per chunk
    TRANSLATION_TEMPERATURE: float = 0.3

    # System prompt for translation
    TRANSLATION_SYSTEM_PROMPT: str = (
        "You are a professional subtitle translator. "
        "Translate the provided text into natural, fluent French. "
        "Keep the exact original meaning and tone. "
        "Do not add any extra commentary, notes, or conversational text. "
        "Return ONLY the translated text, nothing else. "
        "Maintain the same number of lines as the input."
    )

    # Supported video extensions
    SUPPORTED_EXTENSIONS: list[str] = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"]

    # Paths
    UPLOAD_DIR: str = os.path.join(tempfile.gettempdir(), "subtranslate", "uploads")
    OUTPUT_DIR: str = os.path.join(tempfile.gettempdir(), "subtranslate", "output")

    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    @staticmethod
    def detect_device() -> str:
        """Detect the best available compute device."""
        system = platform.system()

        if system == "Darwin":
            # macOS — check for Apple Silicon
            if platform.machine() == "arm64":
                try:
                    import torch
                    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        return "mps"
                except ImportError:
                    pass
                # faster-whisper can use CoreML or MPS on Apple Silicon
                return "auto"
            return "cpu"

        # Linux / Windows — check for CUDA
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass

        return "auto"

    @staticmethod
    def get_ffmpeg_path() -> str:
        """Get FFmpeg binary path."""
        # 1. Check env var (set by Electron in packaged mode)
        env_path = os.environ.get("SUBTRANSLATE_FFMPEG_PATH")
        if env_path and os.path.isfile(env_path):
            return env_path

        # 2. Check for bundled FFmpeg relative to this file (dev mode)
        if platform.system() == "Darwin":
            bundled = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "ffmpeg")
        else:
            bundled = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "ffmpeg.exe")

        if os.path.isfile(bundled):
            return bundled

        # 3. Fallback to system FFmpeg
        return "ffmpeg"


settings = Settings()