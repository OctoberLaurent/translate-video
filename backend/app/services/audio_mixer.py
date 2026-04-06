"""Audio mixer service — assemble TTS segments and replace audio in video."""
import asyncio
import os
import logging
import subprocess
import tempfile

from app.utils.config import settings

logger = logging.getLogger(__name__)


class AudioMixer:
    """Mix TTS audio segments into a dubbed audio track and replace video audio."""

    @staticmethod
    async def adjust_segment_speed(
        input_path: str,
        target_duration: float,
        output_path: str,
    ) -> str:
        """
        Adjust the speed of a TTS segment to match the original segment duration.

        Uses FFmpeg atempo filter. The atempo filter range is [0.5, 100.0].
        For ratios outside this range, we chain multiple atempo filters.

        Args:
            input_path: Path to the TTS audio segment.
            target_duration: Desired duration in seconds.
            output_path: Path for the adjusted audio file.

        Returns:
            Path to the adjusted audio file.
        """
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Get actual duration
        actual_duration = AudioMixer._get_audio_duration(input_path)

        if actual_duration <= 0 or target_duration <= 0:
            AudioMixer._copy_file(input_path, output_path)
            return output_path

        speed_ratio = actual_duration / target_duration

        # If the difference is negligible (<5%), keep original
        if abs(speed_ratio - 1.0) < 0.05:
            AudioMixer._copy_file(input_path, output_path)
            return output_path

        # Clamp speed ratio to reasonable range [0.5, 2.0]
        speed_ratio = max(0.5, min(2.0, speed_ratio))

        # Build atempo filter chain for ratios outside [0.5, 2.0]
        atempo_filters = AudioMixer._build_atempo_chain(speed_ratio)

        ffmpeg_path = settings.get_ffmpeg_path()
        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-filter:a", atempo_filters,
            "-acodec", "pcm_s16le",
            "-ar", "24000",
            "-ac", "1",
            "-y",
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
                logger.warning(f"Speed adjustment failed, using original: {stderr.decode()[:200]}")
                AudioMixer._copy_file(input_path, output_path)

            return output_path

        except Exception as e:
            logger.warning(f"Speed adjustment error: {e}, using original")
            AudioMixer._copy_file(input_path, output_path)
            return output_path

    @staticmethod
    async def build_dubbed_audio(
        tts_results: list[dict],
        output_path: str,
        total_duration: float | None = None,
        progress_callback=None,
    ) -> str:
        """
        Assemble TTS segments into a single dubbed audio track.

        Uses a concat-based approach: for each segment, generate a padded audio
        file (silence before + speech + silence after to fill the segment slot),
        then concatenate all padded segments into the final track.

        Args:
            tts_results: List of TTS result dicts from TTSService.
            output_path: Path for the final dubbed audio WAV file.
            total_duration: Total duration of the original audio (optional).
            progress_callback: Optional async callback(current, total, message).

        Returns:
            Path to the dubbed audio file.
        """
        if not tts_results:
            raise ValueError("No TTS segments to assemble")

        ffmpeg_path = settings.get_ffmpeg_path()
        temp_dir = os.path.dirname(output_path)
        os.makedirs(temp_dir, exist_ok=True)

        if total_duration is None:
            total_duration = tts_results[-1]["end"] + 1.0

        # Step 1: Adjust each segment speed and create padded segments
        padded_dir = os.path.join(temp_dir, "padded")
        os.makedirs(padded_dir, exist_ok=True)

        padded_files = []
        total = len(tts_results)

        prev_end = 0.0

        for i, seg in enumerate(tts_results):
            start = seg["start"]
            end = seg["end"]
            segment_duration = end - start

            # Calculate gap between previous segment and this one
            gap_before = max(0.0, start - prev_end)
            prev_end = end

            # Adjust TTS speed to fit the segment duration
            adjusted_path = os.path.join(padded_dir, f"adj_{i:04d}.wav")
            await AudioMixer.adjust_segment_speed(
                seg["audio_path"],
                segment_duration,
                adjusted_path,
            )

            # Create padded segment: gap silence + adjusted speech
            padded_path = os.path.join(padded_dir, f"padded_{i:04d}.wav")

            if gap_before > 0.01:
                # Add silence gap before the speech
                cmd = [
                    ffmpeg_path,
                    "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
                    "-t", str(gap_before),
                    "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1",
                    "-y",
                    os.path.join(padded_dir, f"silence_{i:04d}.wav"),
                ]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.communicate()

                # Concatenate silence + adjusted speech
                concat_file = os.path.join(padded_dir, f"concat_{i:04d}.txt")
                silence_file = os.path.join(padded_dir, f"silence_{i:04d}.wav")
                with open(concat_file, "w") as f:
                    f.write(f"file '{silence_file}'\n")
                    f.write(f"file '{adjusted_path}'\n")

                cmd = [
                    ffmpeg_path,
                    "-f", "concat", "-safe", "0",
                    "-i", concat_file,
                    "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1",
                    "-y",
                    padded_path,
                ]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    logger.warning(f"Padding concat failed for segment {i}: {stderr.decode()[:200]}")
                    AudioMixer._copy_file(adjusted_path, padded_path)
            else:
                # No gap needed, just copy the adjusted segment
                AudioMixer._copy_file(adjusted_path, padded_path)

            padded_files.append(padded_path)

            if progress_callback:
                await progress_callback(i + 1, total, f"Préparation audio : segment {i + 1}/{total}")

        # Step 2: Concatenate all padded segments into the final track
        concat_file = os.path.join(temp_dir, "final_concat.txt")
        with open(concat_file, "w") as f:
            for pf in padded_files:
                # Escape single quotes in path
                safe_path = pf.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")

        cmd = [
            ffmpeg_path,
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1",
            "-y",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Final concat failed: {error_msg}")

        # Verify the output file exists and has content
        if not os.path.isfile(output_path) or os.path.getsize(output_path) < 100:
            raise RuntimeError("Dubbed audio file is empty or missing")

        logger.info(f"Dubbed audio created: {output_path} ({os.path.getsize(output_path)} bytes)")
        return output_path

    @staticmethod
    async def replace_audio_track(
        video_path: str,
        dubbed_audio_path: str,
        output_path: str,
    ) -> str:
        """
        Replace the audio track of a video with the dubbed audio.

        Keeps the original video track intact.

        Args:
            video_path: Path to the original video.
            dubbed_audio_path: Path to the dubbed WAV audio file.
            output_path: Path for the output video with dubbed audio.

        Returns:
            Path to the output video.
        """
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not os.path.isfile(dubbed_audio_path):
            raise FileNotFoundError(f"Dubbed audio not found: {dubbed_audio_path}")

        ffmpeg_path = settings.get_ffmpeg_path()

        cmd = [
            ffmpeg_path,
            "-i", video_path,
            "-i", dubbed_audio_path,
            "-c:v", "copy",          # Copy video stream as-is
            "-c:a", "aac",           # Encode audio as AAC
            "-b:a", "192k",          # Audio bitrate
            "-map", "0:v:0",         # Use video from first input
            "-map", "1:a:0",         # Use audio from second input (dubbed)
            "-shortest",             # Stop when shortest stream ends
            "-y",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Audio replacement failed: {error_msg}")

        return output_path

    @staticmethod
    def _build_atempo_chain(speed_ratio: float) -> str:
        """
        Build FFmpeg atempo filter chain for the given speed ratio.

        The atempo filter only accepts values between 0.5 and 100.0.
        For values outside this range, we chain multiple filters.

        Args:
            speed_ratio: The speed multiplier (actual_duration / target_duration).

        Returns:
            FFmpeg filter string.
        """
        if 0.5 <= speed_ratio <= 2.0:
            return f"atempo={speed_ratio:.4f}"

        # Chain multiple atempo filters for extreme ratios
        filters = []
        remaining = speed_ratio

        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0

        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5

        filters.append(f"atempo={remaining:.4f}")
        return ",".join(filters)

    @staticmethod
    def _get_audio_duration(file_path: str) -> float:
        """Get the duration of an audio file using ffprobe."""
        ffprobe_path = settings.get_ffmpeg_path().replace("ffmpeg", "ffprobe")
        if not os.path.isfile(ffprobe_path):
            ffprobe_path = "ffprobe"

        cmd = [
            ffprobe_path,
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            try:
                file_size = os.path.getsize(file_path)
                # WAV: 44 byte header + pcm_s16le 24000Hz mono = 48000 bytes/sec
                return max(0.0, (file_size - 44) / 48000)
            except OSError:
                return 0.0

    @staticmethod
    def _copy_file(src: str, dst: str):
        """Copy a file."""
        import shutil
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)