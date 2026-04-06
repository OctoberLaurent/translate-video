"""SRT file builder service."""
import os
import re
import logging
from pathlib import Path

from app.utils.config import settings

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
    def merge_segments(
        segments: list[dict],
        max_chars: int | None = None,
        max_duration: float | None = None,
    ) -> list[dict]:
        """
        Merge short Whisper segments into natural subtitle lines.

        Whisper often cuts mid-sentence. This method merges consecutive segments
        until a sentence-ending punctuation is encountered, while respecting
        character and duration limits.

        Args:
            segments: List of dicts with 'index', 'start', 'end', 'text'.
            max_chars: Maximum characters per merged subtitle (default from settings).
            max_duration: Maximum duration in seconds (default from settings).

        Returns:
            New list of merged segments with renumbered indices.
        """
        if not segments:
            return []

        max_chars = max_chars or settings.SRT_MAX_CHARS
        max_duration = max_duration or settings.SRT_MAX_DURATION

        if not settings.SRT_MERGE_ENABLED:
            # Just renumber and return
            return [
                {**s, "index": i}
                for i, s in enumerate(segments)
            ]

        # Sentence-ending punctuation
        sentence_end_re = re.compile(r'[.!?…]\s*$')
        # Secondary punctuation (good split points within a sentence)
        secondary_punct_re = re.compile(r'[,;:—–]\s*')

        merged: list[dict] = []
        i = 0

        while i < len(segments):
            seg = segments[i]
            current_text = seg["text"].strip()
            current_start = seg["start"]
            current_end = seg["end"]

            # If this segment alone exceeds max_chars, try to split it
            if len(current_text) > max_chars:
                split_parts = SRTBuilder._split_long_segment(
                    seg, max_chars, secondary_punct_re
                )
                for part in split_parts:
                    merged.append(part)
                i += 1
                continue

            # If already ends a sentence, don't try to merge
            if sentence_end_re.search(current_text):
                merged.append({
                    "index": len(merged),
                    "start": current_start,
                    "end": current_end,
                    "text": current_text,
                })
                i += 1
                continue

            # Try to merge with following segments
            j = i + 1
            while j < len(segments):
                next_seg = segments[j]
                candidate_text = current_text + " " + next_seg["text"].strip()
                candidate_duration = next_seg["end"] - current_start

                # Stop if we exceed limits
                if len(candidate_text) > max_chars:
                    break
                if candidate_duration > max_duration:
                    break

                # Accept the merge
                current_text = candidate_text
                current_end = next_seg["end"]
                j += 1

                # Stop if we've reached a sentence end
                if sentence_end_re.search(next_seg["text"].strip()):
                    break

            merged.append({
                "index": len(merged),
                "start": current_start,
                "end": current_end,
                "text": current_text,
            })
            i = j

        # Renumber indices
        for idx, seg in enumerate(merged):
            seg["index"] = idx

        logger.info(
            f"Segment merging: {len(segments)} → {len(merged)} segments "
            f"(max_chars={max_chars}, max_duration={max_duration}s)"
        )

        return merged

    @staticmethod
    def _split_long_segment(
        segment: dict,
        max_chars: int,
        punct_re: re.Pattern,
    ) -> list[dict]:
        """
        Split a single segment that exceeds max_chars into multiple parts.

        Tries to split at punctuation marks first, then at word boundaries.

        Args:
            segment: A single segment dict with 'start', 'end', 'text'.
            max_chars: Maximum characters per part.
            punct_re: Compiled regex for secondary punctuation split points.

        Returns:
            List of segment dicts.
        """
        text = segment["text"].strip()
        duration = segment["end"] - segment["start"]
        results: list[dict] = []

        # Find all punctuation split positions
        split_positions = []
        for match in punct_re.finditer(text):
            split_positions.append(match.end())

        # Also split at whitespace (word boundaries) as fallback
        for match in re.finditer(r'\s+', text):
            split_positions.append(match.start())

        # Deduplicate and sort
        split_positions = sorted(set(split_positions))

        # Filter to only positions within max_chars
        current_start_pos = 0
        while current_start_pos < len(text):
            # Find the best split position within max_chars
            best_split = None
            for pos in split_positions:
                if pos <= current_start_pos:
                    continue
                if pos - current_start_pos > max_chars:
                    break
                best_split = pos

            if best_split is None or best_split <= current_start_pos:
                # No good split found; hard-cut at max_chars at last space
                if len(text) - current_start_pos <= max_chars:
                    part_text = text[current_start_pos:].strip()
                    if part_text:
                        results.append(part_text)
                    break
                else:
                    # Find last space before max_chars
                    chunk = text[current_start_pos:current_start_pos + max_chars]
                    last_space = chunk.rfind(' ')
                    if last_space > 0:
                        best_split = current_start_pos + last_space
                    else:
                        best_split = current_start_pos + max_chars

            part_text = text[current_start_pos:best_split].strip()
            if part_text:
                results.append(part_text)
            current_start_pos = best_split

        # Distribute timestamps proportionally across parts
        total_chars = len(text)
        part_results = []
        elapsed = 0.0

        for part_idx, part_text in enumerate(results):
            part_chars = len(part_text)
            proportion = part_chars / total_chars if total_chars > 0 else 1.0 / len(results)

            part_start = segment["start"] + elapsed
            part_duration = duration * proportion
            part_end = part_start + part_duration

            # Make sure last segment ends at original end
            if part_idx == len(results) - 1:
                part_end = segment["end"]

            part_results.append({
                "index": 0,  # Will be renumbered by merge_segments
                "start": part_start,
                "end": part_end,
                "text": part_text,
            })
            elapsed += part_duration

        return part_results

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
