"""Whisper transcription service using faster-whisper."""
import os
import logging
from dataclasses import dataclass

from app.utils.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSegment:
    """A single transcription segment with timing information."""
    index: int
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text


@dataclass
class TranscriptionResult:
    """Complete transcription result containing all segments."""
    segments: list[TranscriptionSegment]
    detected_language: str
    duration: float


class WhisperService:
    """Handle audio transcription using faster-whisper."""

    def __init__(self, model_size: str | None = None, device: str | None = None):
        """
        Initialize Whisper service.

        Args:
            model_size: Whisper model size (base, small, medium, large-v3).
            device: Compute device (cuda, mps, cpu, auto).
        """
        self.model_size = model_size or settings.WHISPER_DEFAULT_MODEL
        self.device = device or settings.detect_device()
        self._model = None

    def _load_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            logger.info(f"Loading Whisper model '{self.model_size}' on device '{self.device}'")
            from faster_whisper import WhisperModel

            compute_type = "float16" if self.device == "cuda" else "int8"

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=compute_type,
            )
            logger.info(f"Whisper model '{self.model_size}' loaded successfully")

    def transcribe(
        self,
        audio_path: str,
        task: str = "translate",
        language: str | None = None,
        progress_callback: callable = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the WAV audio file.
            task: Either "transcribe" (original language) or "translate" (to English).
            language: Force a specific language (None for auto-detect).
            progress_callback: Optional callback(current_pct, message) for progress updates.
            
        Returns:
            TranscriptionResult with all segments and metadata.
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        logger.info(f"Starting transcription of '{audio_path}' (task={task})")

        # Transcribe with word-level timestamps for better alignment
        segments_generator, info = self._model.transcribe(
            audio_path,
            task=task,
            language=language,
            beam_size=5,
            vad_filter=False,  # Disabled — too aggressive for whispered/ASMR audio, causing all speech to be filtered out
        )

        total_duration = info.duration  # Get total audio duration early
        segments = []
        for i, segment in enumerate(segments_generator):
            segments.append(
                TranscriptionSegment(
                    index=i,
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                )
            )
            
            # Send progress based on current position in audio
            if progress_callback and total_duration > 0:
                pct = min(int((segment.end / total_duration) * 100), 99)
                progress_callback(pct, f"Transcription : {pct}% ({i + 1} segments)")
            elif i % 50 == 0:
                logger.info(f"Transcribed {i} segments...")

        detected_language = info.language
        duration = info.duration

        logger.info(
            f"Transcription complete: {len(segments)} segments, "
            f"language={detected_language}, duration={duration:.1f}s"
        )

        return TranscriptionResult(
            segments=segments,
            detected_language=detected_language,
            duration=duration,
        )

    def unload_model(self):
        """Unload the model to free memory."""
        self._model = None
        logger.info("Whisper model unloaded")