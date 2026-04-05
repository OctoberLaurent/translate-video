"""SRT file builder service."""
import os
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SRTBuilder:
    """Build SRT subtitle files from translated segments."""

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Convert seconds to SRT timestamp format: HH:MM:SS,mmm

        Args:
            seconds: Time in seconds (float).

        Returns:
            Formatted timestamp string.
        """
        if seconds < 0:
            seconds = 0.0

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def build_srt(
        segments: list[dict],
        translated_texts: list[str],
        output_path: str,
    ) -> str:
        """
        Build an SRT file from segments and their translations.

        Args:
            segments: List of dicts with 'index', 'start', 'end', 'text' keys.
            translated_texts: List of translated text strings (same order as segments).
            output_path: Path where the SRT file will be written.

        Returns:
            Path to the generated SRT file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        lines = []
        for i, segment in enumerate(segments):
            # SRT index (1-based)
            srt_index = i + 1

            # Format timestamps
            start_ts = SRTBuilder.format_timestamp(segment["start"])
            end_ts = SRTBuilder.format_timestamp(segment["end"])

            # Get translated text (fallback to original if translation missing)
            text = translated_texts[i].strip() if i < len(translated_texts) else segment["text"]

            # Skip empty segments
            if not text:
                continue

            # Build SRT block
            lines.append(str(srt_index))
            lines.append(f"{start_ts} --> {end_ts}")
            lines.append(text)
            lines.append("")  # Blank line between entries

        srt_content = "\n".join(lines)

        # Ensure UTF-8 encoding with BOM for better compatibility
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        logger.info(f"SRT file written to '{output_path}' ({len(segments)} entries)")
        return output_path

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Sanitize a filename for safe use in URLs and file systems.

        - URL-decodes any %XX sequences (e.g. %22 → ")
        - Removes characters unsafe in URLs: ?, #, %, quotes, <, >, backslash, ^, comma
        - Replaces multiple spaces/underscores with a single underscore

        Args:
            name: Raw filename (without extension).

        Returns:
            Sanitized filename.
        """
        # URL-decode any percent-encoded sequences
        decoded = re.sub(r'%[0-9A-Fa-f]{2}', lambda m: chr(int(m.group()[1:], 16)), name)

        # Remove characters that are problematic in URLs or file systems
        sanitized = re.sub(r'[?#"\'<>\\^%,]', '', decoded)

        # Replace multiple whitespace with single underscore
        sanitized = re.sub(r'\s+', '_', sanitized.strip())

        # Remove leading/trailing dots
        sanitized = sanitized.strip('.')

        return sanitized

    @staticmethod
    def generate_output_path(video_path: str, output_dir: str) -> str:
        """
        Generate the output SRT file path based on the video filename.

        The filename is sanitized to avoid characters that break URL routing
        (%, ?, #, quotes, etc.).

        Args:
            video_path: Original video file path.
            output_dir: Directory where the SRT should be saved.

        Returns:
            Full path to the output SRT file.
        """
        video_name = Path(video_path).stem
        safe_name = SRTBuilder.sanitize_filename(video_name)
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, f"{safe_name}.srt")
