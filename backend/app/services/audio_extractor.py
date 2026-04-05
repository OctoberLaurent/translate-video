"""Audio extraction service using FFmpeg."""
import asyncio
import os
import subprocess
from pathlib import Path

from app.utils.config import settings


class AudioExtractor:
    """Extract audio from video files using FFmpeg."""

    @staticmethod
    async def extract(video_path: str, output_path: str | None = None) -> str:
        """
        Extract audio from a video file and convert to WAV 16kHz mono.

        Args:
            video_path: Path to the input video file.
            output_path: Optional output path. Defaults to same dir as video.

        Returns:
            Path to the extracted WAV file.

        Raises:
            FileNotFoundError: If the video file doesn't exist.
            RuntimeError: If FFmpeg extraction fails.
        """
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Determine output path
        if output_path is None:
            video_name = Path(video_path).stem
            output_path = os.path.join(settings.UPLOAD_DIR, f"{video_name}.wav")

        ffmpeg_path = settings.get_ffmpeg_path()

        cmd = [
            ffmpeg_path,
            "-i", video_path,
            "-vn",                    # No video
            "-acodec", "pcm_s16le",   # 16-bit PCM
            "-ar", "16000",           # 16 kHz sample rate
            "-ac", "1",               # Mono
            "-y",                     # Overwrite output
            output_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                raise RuntimeError(f"FFmpeg extraction failed: {error_msg}")

            if not os.path.isfile(output_path):
                raise RuntimeError("FFmpeg completed but output file not found")

            return output_path

        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg or ensure it is bundled with the application."
            )