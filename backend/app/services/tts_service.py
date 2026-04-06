"""
Text-to-Speech service with multiple backend support.

Backends:
  - edge-tts: Microsoft Edge TTS (online, excellent French voices, Python 3.12+)
  - coqui: Coqui TTS / XTTSv2 (local, requires Python <3.12, optional)
"""
import asyncio
import os
import logging
import re

from app.utils.config import settings

logger = logging.getLogger(__name__)

# French voices for edge-tts
EDGE_TTS_FRENCH_VOICES = [
    "fr-FR-DeniseNeural",      # Female, standard
    "fr-FR-HenriNeural",       # Male, standard
    "fr-FR-EloiseNeural",      # Female, multilingual
    "fr-FR-JeanNeural",        # Male, standard
    "fr-FR-SuzanneNeural",     # Female, standard
    "fr-BE-CharlineNeural",    # Belgian French female
    "fr-CA-ThierryNeural",     # Canadian French male
    "fr-CA-SylvieNeural",      # Canadian French female
    "fr-CH-ArianeNeural",      # Swiss French female
    "fr-CH-GuillaumeNeural",   # Swiss French male
]


class TTSService:
    """Synthesize speech from text using edge-tts or Coqui TTS."""

    def __init__(
        self,
        backend: str | None = None,
        voice: str | None = None,
        language: str | None = None,
    ):
        """
        Initialize TTS service.

        Args:
            backend: 'edge-tts' or 'coqui'. Auto-detected if None.
            voice: Voice name (e.g. 'fr-FR-DeniseNeural' for edge-tts).
            language: Language code (e.g. 'fr').
        """
        self.language = language or settings.TTS_LANGUAGE
        self.voice = voice or "fr-FR-DeniseNeural"
        self._coqui_model = None

        # Auto-detect backend
        if backend:
            self.backend = backend
        else:
            self.backend = self._detect_backend()

        logger.info(f"TTS backend: {self.backend}, voice: {self.voice}")

    @staticmethod
    def _detect_backend() -> str:
        """Detect the best available TTS backend."""
        try:
            import edge_tts
            return "edge-tts"
        except ImportError:
            pass

        try:
            from TTS.api import TTS
            return "coqui"
        except ImportError:
            pass

        raise RuntimeError(
            "Aucun moteur TTS disponible. Installez edge-tts (pip install edge-tts) "
            "ou Coqui TTS (pip install TTS, nécessite Python <3.12)."
        )

    async def synthesize_segment(
        self,
        text: str,
        output_path: str,
    ) -> str:
        """
        Synthesize a single text segment to an audio file.

        Args:
            text: The text to synthesize.
            output_path: Path where the audio file will be saved.

        Returns:
            Path to the generated audio file.
        """
        clean_text = self._clean_text(text)

        if not clean_text.strip():
            self._generate_silence(output_path, duration=0.5)
            return output_path

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.backend == "edge-tts":
            return await self._synthesize_edge(clean_text, output_path)
        elif self.backend == "coqui":
            return await self._synthesize_coqui(clean_text, output_path)
        else:
            raise RuntimeError(f"Unknown TTS backend: {self.backend}")

    async def synthesize_segments_batch(
        self,
        segments: list[dict],
        translated_texts: list[str],
        output_dir: str,
        progress_callback=None,
    ) -> list[dict]:
        """
        Synthesize all segments to individual audio files.

        Args:
            segments: List of segment dicts with 'index', 'start', 'end' keys.
            translated_texts: List of translated text strings.
            output_dir: Directory to store segment audio files.
            progress_callback: Optional async callback(current, total, message).

        Returns:
            List of dicts with segment info and audio paths.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Load model for coqui backend
        if self.backend == "coqui":
            self._load_coqui_model()

        results = []
        total = len(segments)

        for i, segment in enumerate(segments):
            text = translated_texts[i].strip() if i < len(translated_texts) else ""
            output_path = os.path.join(output_dir, f"segment_{i:04d}.mp3")

            await self.synthesize_segment(text, output_path)

            # Get actual duration of generated audio
            duration = self._get_audio_duration(output_path)
            original_duration = segment["end"] - segment["start"]

            results.append({
                "index": i,
                "start": segment["start"],
                "end": segment["end"],
                "original_duration": original_duration,
                "tts_duration": duration,
                "audio_path": output_path,
                "text": text,
            })

            if progress_callback:
                if asyncio.iscoroutinefunction(progress_callback):
                    await progress_callback(i + 1, total, f"Synthèse vocale : segment {i + 1}/{total}")
                else:
                    progress_callback(i + 1, total, f"Synthèse vocale : segment {i + 1}/{total}")

        # Unload coqui model if loaded
        if self.backend == "coqui":
            self._unload_coqui_model()

        return results

    # ── Edge TTS Backend ──────────────────────────────────────────────

    async def _synthesize_edge(self, text: str, output_path: str, _retry_count: int = 0) -> str:
        """Synthesize using Microsoft Edge TTS (async) with retry and voice fallback."""
        import edge_tts

        max_retries = 3
        base_delay = 2.0

        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)

            # Verify the output file has content
            if os.path.getsize(output_path) < 100:
                raise RuntimeError("Output file too small — likely empty audio")

            return output_path

        except Exception as e:
            logger.warning(f"Edge TTS attempt {_retry_count + 1} failed for '{text[:50]}...': {e}")

            if _retry_count < max_retries:
                delay = base_delay * (_retry_count + 1)

                # On 2nd retry, try a different voice
                if _retry_count == 1:
                    fallback_voice = self._get_fallback_voice()
                    if fallback_voice != self.voice:
                        logger.info(f"Retrying with fallback voice: {fallback_voice}")
                        original_voice = self.voice
                        self.voice = fallback_voice
                        result = await self._synthesize_edge(text, output_path, _retry_count + 1)
                        self.voice = original_voice
                        return result

                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
                return await self._synthesize_edge(text, output_path, _retry_count + 1)
            else:
                logger.error(f"Edge TTS failed after {max_retries} retries for '{text[:50]}...': {e}")
                self._generate_silence(output_path, duration=1.0)
                return output_path

    def _get_fallback_voice(self) -> str:
        """Get a fallback voice different from the current one."""
        # Prefer Denise as most reliable fallback
        fallback_order = ["fr-FR-DeniseNeural", "fr-FR-HenriNeural", "fr-FR-EloiseNeural"]
        for voice in fallback_order:
            if voice != self.voice:
                return voice
        return self.voice

    # ── Coqui TTS Backend ─────────────────────────────────────────────

    def _load_coqui_model(self):
        """Load Coqui TTS model into memory."""
        if self._coqui_model is not None:
            return

        try:
            from TTS.api import TTS as CoquiTTS
            import torch

            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

            model_name = settings.TTS_MODEL
            logger.info(f"Loading Coqui TTS model: {model_name} on {device}")

            self._coqui_model = CoquiTTS(model_name=model_name).to(device)
            logger.info("Coqui TTS model loaded successfully")

        except Exception as e:
            self._coqui_model = None
            raise RuntimeError(f"Failed to load Coqui TTS model: {e}")

    def _unload_coqui_model(self):
        """Unload Coqui TTS model to free memory."""
        if self._coqui_model is not None:
            del self._coqui_model
            self._coqui_model = None

            import gc
            gc.collect()

            try:
                import torch
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                elif torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.info("Coqui TTS model unloaded")

    async def _synthesize_coqui(self, text: str, output_path: str) -> str:
        """Synthesize using Coqui TTS (runs in executor)."""
        if self._coqui_model is None:
            raise RuntimeError("Coqui TTS model not loaded")

        loop = asyncio.get_event_loop()

        def _sync_synthesize():
            self._coqui_model.tts_to_file(
                text=text,
                language=self.language,
                file_path=output_path,
            )
            return output_path

        try:
            return await loop.run_in_executor(None, _sync_synthesize)
        except Exception as e:
            logger.error(f"Coqui TTS failed for '{text[:50]}...': {e}")
            self._generate_silence(output_path, duration=1.0)
            return output_path

    # ── Utilities ─────────────────────────────────────────────────────

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text for TTS synthesis."""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'^\d+\s*$', '', text)
        return text.strip()

    @staticmethod
    def _generate_silence(output_path: str, duration: float = 1.0):
        """Generate a silent audio file using FFmpeg."""
        import subprocess

        ffmpeg_path = settings.get_ffmpeg_path()
        cmd = [
            ffmpeg_path,
            "-f", "lavfi",
            "-i", f"anullsrc=r=24000:cl=mono",
            "-t", str(duration),
            "-acodec", "libmp3lame",
            "-y",
            output_path,
        ]

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            subprocess.run(cmd, capture_output=True, check=True)
        except Exception as e:
            logger.warning(f"Failed to generate silence: {e}")

    @staticmethod
    def _get_audio_duration(file_path: str) -> float:
        """Get the duration of an audio file using ffprobe."""
        import subprocess

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
            # Fallback: estimate from file size (MP3 ~128kbps)
            try:
                file_size = os.path.getsize(file_path)
                return max(0.0, file_size / (128 * 1000 / 8))
            except OSError:
                return 0.0

    @staticmethod
    def list_voices() -> list[str]:
        """List available French voices for the current backend."""
        return EDGE_TTS_FRENCH_VOICES