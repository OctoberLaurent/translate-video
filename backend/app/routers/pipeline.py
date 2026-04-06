"""Pipeline router — orchestrate the full subtitle generation process."""
import asyncio
import json
import logging
import os
import re
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.services.audio_extractor import AudioExtractor
from app.services.whisper_service import WhisperService
from app.services.translator import TranslatorService
from app.services.srt_builder import SRTBuilder
from app.services.tts_service import TTSService
from app.services.audio_mixer import AudioMixer
from app.utils.config import settings

router = APIRouter(prefix="/api", tags=["pipeline"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for pipeline progress."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_progress(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_json(data)
        except Exception:
            pass


manager = ConnectionManager()


@router.websocket("/ws/pipeline")
async def pipeline_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for running the subtitle generation pipeline.

    Expected message format:
    {
        "file_path": "/path/to/video.mp4",
        "whisper_model": "base",
        "llm_model": "model-id",
        "whisper_task": "translate",
        "lm_studio_port": 7890,
        "translation_prompt": "..."
    }
    """
    await manager.connect(websocket)

    try:
        config = await websocket.receive_json()

        file_path = config.get("file_path")
        whisper_model = config.get("whisper_model", settings.WHISPER_DEFAULT_MODEL)
        llm_model = config.get("llm_model")
        whisper_task = config.get("whisper_task", "translate")
        lm_studio_port = config.get("lm_studio_port")
        translation_prompt = config.get("translation_prompt")

        if not file_path:
            await websocket.send_json({
                "type": "error",
                "step": "config",
                "message": "Chemin du fichier manquant.",
            })
            return

        await run_pipeline(
            websocket, file_path, whisper_model, llm_model,
            whisper_task, lm_studio_port, translation_prompt,
        )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "step": "pipeline",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        manager.disconnect(websocket)


async def run_pipeline(
    websocket: WebSocket,
    file_path: str,
    whisper_model: str,
    llm_model: str | None,
    whisper_task: str,
    lm_studio_port: int | None = None,
    translation_prompt: str | None = None,
):
    """Execute the 4-step subtitle pipeline: extract, transcribe, translate, srt."""

    total_steps = 4

    # --- Step 1: Audio Extraction ---
    await websocket.send_json({
        "type": "progress",
        "step": "extraction",
        "step_number": 1,
        "total_steps": total_steps,
        "message": "Extraction de l'audio en cours...",
        "progress": 0,
    })

    try:
        audio_path = await AudioExtractor.extract(file_path)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "step": "extraction",
            "message": f"Erreur lors de l'extraction audio : {e}",
        })
        return

    await websocket.send_json({
        "type": "progress",
        "step": "extraction",
        "step_number": 1,
        "total_steps": total_steps,
        "message": "Audio extrait avec succès ✓",
        "progress": 100,
    })

    # --- Step 2: Whisper Transcription ---
    await websocket.send_json({
        "type": "progress",
        "step": "transcription",
        "step_number": 2,
        "total_steps": total_steps,
        "message": f"Transcription avec Whisper ({whisper_model}) en cours...",
        "progress": 0,
    })

    try:
        whisper = WhisperService(model_size=whisper_model)
        loop = asyncio.get_event_loop()

        def on_whisper_progress(pct: int, message: str):
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({
                    "type": "progress",
                    "step": "transcription",
                    "step_number": 2,
                    "total_steps": total_steps,
                    "message": message,
                    "progress": pct,
                }),
                loop,
            )

        result = await loop.run_in_executor(
            None,
            lambda: whisper.transcribe(audio_path, task=whisper_task, progress_callback=on_whisper_progress),
        )
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "step": "transcription",
            "message": f"Erreur lors de la transcription : {e}",
        })
        return

    segment_count = len(result.segments)

    await websocket.send_json({
        "type": "progress",
        "step": "transcription",
        "step_number": 2,
        "total_steps": total_steps,
        "message": f"Transcription terminée ✓ ({segment_count} segments, langue: {result.detected_language})",
        "progress": 100,
        "data": {
            "segment_count": segment_count,
            "detected_language": result.detected_language,
            "duration": result.duration,
        },
    })

    segments = [
        {"index": s.index, "start": s.start, "end": s.end, "text": s.text}
        for s in result.segments
    ]

    whisper.unload_model()

    # --- Step 3: Translation via LM Studio ---
    await websocket.send_json({
        "type": "progress",
        "step": "translation",
        "step_number": 3,
        "total_steps": total_steps,
        "message": "Traduction en cours via LM Studio...",
        "progress": 0,
    })

    try:
        translator = TranslatorService(model=llm_model, port=lm_studio_port, custom_prompt=translation_prompt)
        chunks = translator._create_chunks(segments)
        total_chunks = len(chunks)
        translated_texts = [""] * len(segments)

        async with __import__("httpx").AsyncClient(timeout=translator.timeout) as client:
            for chunk_idx, chunk in enumerate(chunks):
                chunk_text = "\n".join(f"[{s['index']}] {s['text']}" for s in chunk)
                translated = await translator._translate_chunk(client, chunk_text)
                translated_lines = translator._parse_translated_lines(translated, len(chunk))

                for i, segment in enumerate(chunk):
                    orig_idx = segment["index"]
                    if i < len(translated_lines):
                        translated_texts[orig_idx] = translated_lines[i]
                    else:
                        translated_texts[orig_idx] = segment["text"]

                progress_pct = int(((chunk_idx + 1) / total_chunks) * 100)
                await websocket.send_json({
                    "type": "progress",
                    "step": "translation",
                    "step_number": 3,
                    "total_steps": total_steps,
                    "message": f"Traduction : bloc {chunk_idx + 1}/{total_chunks}",
                    "progress": progress_pct,
                })

    except ConnectionError as e:
        await websocket.send_json({"type": "error", "step": "translation", "message": str(e)})
        return
    except Exception as e:
        await websocket.send_json({"type": "error", "step": "translation", "message": f"Erreur lors de la traduction : {e}"})
        return

    await websocket.send_json({
        "type": "progress",
        "step": "translation",
        "step_number": 3,
        "total_steps": total_steps,
        "message": "Traduction terminée ✓",
        "progress": 100,
    })

    # --- Step 4: SRT Assembly ---
    await websocket.send_json({
        "type": "progress",
        "step": "srt",
        "step_number": 4,
        "total_steps": total_steps,
        "message": "Assemblage du fichier SRT...",
        "progress": 0,
    })

    try:
        srt_path = SRTBuilder.generate_output_path(file_path, settings.OUTPUT_DIR)
        SRTBuilder.build_srt(segments, translated_texts, srt_path)
    except Exception as e:
        await websocket.send_json({"type": "error", "step": "srt", "message": f"Erreur lors de l'assemblage SRT : {e}"})
        return

    await websocket.send_json({
        "type": "progress",
        "step": "srt",
        "step_number": 4,
        "total_steps": total_steps,
        "message": "Fichier SRT généré ✓",
        "progress": 100,
    })

    # --- Done ---
    await websocket.send_json({
        "type": "complete",
        "step": "done",
        "message": "Sous-titres générés avec succès !",
        "data": {
            "srt_path": srt_path,
            "segment_count": segment_count,
            "detected_language": result.detected_language,
            "video_path": file_path,
        },
    })


@router.websocket("/ws/tts")
async def tts_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for running TTS dubbing on an existing SRT.

    Expected message format:
    {
        "srt_path": "/path/to/file.srt",
        "video_path": "/path/to/video.mp4",
        "voice": "fr-FR-DeniseNeural"
    }
    """
    await manager.connect(websocket)

    try:
        config = await websocket.receive_json()

        srt_path = config.get("srt_path")
        video_path = config.get("video_path", "")
        tts_model = config.get("tts_model")
        voice = config.get("voice")

        if not srt_path:
            await websocket.send_json({"type": "error", "step": "config", "message": "Chemin du fichier SRT manquant."})
            return

        await run_tts_pipeline(websocket, srt_path, video_path or None, tts_model, voice)

    except WebSocketDisconnect:
        logger.info("TTS WebSocket disconnected")
    except Exception as e:
        logger.error(f"TTS Pipeline error: {e}")
        try:
            await websocket.send_json({"type": "error", "step": "pipeline", "message": str(e)})
        except Exception:
            pass
    finally:
        manager.disconnect(websocket)


async def run_tts_pipeline(
    websocket: WebSocket,
    srt_path: str,
    video_path: str | None,
    tts_model: str | None = None,
    voice: str | None = None,
):
    """Execute the TTS dubbing pipeline with progress updates."""

    has_video = bool(video_path and os.path.isfile(video_path))
    total_steps = 4 if has_video else 3

    # --- Step 1: Parse SRT file ---
    await websocket.send_json({
        "type": "progress", "step": "parse_srt", "step_number": 1,
        "total_steps": total_steps, "message": "Lecture du fichier SRT...", "progress": 0,
    })

    try:
        segments, translated_texts = parse_srt_file(srt_path)
        segment_count = len(segments)
    except Exception as e:
        await websocket.send_json({"type": "error", "step": "parse_srt", "message": f"Erreur lors de la lecture du SRT : {e}"})
        return

    if segment_count == 0:
        await websocket.send_json({"type": "error", "step": "parse_srt", "message": "Le fichier SRT ne contient aucun segment."})
        return

    await websocket.send_json({
        "type": "progress", "step": "parse_srt", "step_number": 1,
        "total_steps": total_steps, "message": f"SRT lu ✓ ({segment_count} segments)", "progress": 100,
    })

    # --- Step 2: TTS Synthesis ---
    await websocket.send_json({
        "type": "progress", "step": "tts_synthesis", "step_number": 2,
        "total_steps": total_steps, "message": "Chargement du modèle TTS...", "progress": 0,
    })

    try:
        tts = TTSService(backend=tts_model, voice=voice)
        tts_temp_dir = os.path.join(settings.TTS_TEMP_DIR, os.path.basename(srt_path).replace(".srt", ""))
        os.makedirs(tts_temp_dir, exist_ok=True)

        async def on_tts_progress(current: int, total: int, message: str):
            progress_pct = int((current / total) * 100)
            await websocket.send_json({
                "type": "progress", "step": "tts_synthesis", "step_number": 2,
                "total_steps": total_steps, "message": message, "progress": progress_pct,
            })

        tts_results = await tts.synthesize_segments_batch(
            segments, translated_texts, tts_temp_dir,
            progress_callback=on_tts_progress,
        )
    except Exception as e:
        await websocket.send_json({"type": "error", "step": "tts_synthesis", "message": f"Erreur lors de la synthèse vocale : {e}"})
        return

    await websocket.send_json({
        "type": "progress", "step": "tts_synthesis", "step_number": 2,
        "total_steps": total_steps, "message": f"Synthèse vocale terminée ✓ ({segment_count} segments)", "progress": 100,
    })

    # --- Step 3: Build dubbed audio ---
    await websocket.send_json({
        "type": "progress", "step": "audio_mix", "step_number": 3,
        "total_steps": total_steps, "message": "Assemblage de l'audio doublé...", "progress": 0,
    })

    try:
        video_duration = get_video_duration(video_path) if has_video else 0.0
        dubbed_audio_path = os.path.join(settings.OUTPUT_DIR, os.path.basename(srt_path).replace(".srt", "_dubbed.wav"))

        async def on_mix_progress(current: int, total: int, message: str):
            progress_pct = int((current / total) * 100)
            await websocket.send_json({
                "type": "progress", "step": "audio_mix", "step_number": 3,
                "total_steps": total_steps, "message": message, "progress": progress_pct,
            })

        await AudioMixer.build_dubbed_audio(
            tts_results, dubbed_audio_path,
            total_duration=video_duration,
            progress_callback=on_mix_progress,
        )
    except Exception as e:
        await websocket.send_json({"type": "error", "step": "audio_mix", "message": f"Erreur lors du mixage audio : {e}"})
        return

    await websocket.send_json({
        "type": "progress", "step": "audio_mix", "step_number": 3,
        "total_steps": total_steps, "message": "Audio doublé assemblé ✓", "progress": 100,
    })

    # --- Step 4: Replace audio in video (only if video provided) ---
    dubbed_video_path = None

    if has_video:
        await websocket.send_json({
            "type": "progress", "step": "video_merge", "step_number": 4,
            "total_steps": total_steps, "message": "Remplacement de l'audio dans la vidéo...", "progress": 0,
        })

        try:
            video_name = os.path.basename(video_path)
            dubbed_video_path = os.path.join(
                settings.OUTPUT_DIR,
                os.path.splitext(video_name)[0] + "_dubbed" + os.path.splitext(video_name)[1],
            )
            await AudioMixer.replace_audio_track(video_path, dubbed_audio_path, dubbed_video_path)
        except Exception as e:
            await websocket.send_json({"type": "error", "step": "video_merge", "message": f"Erreur lors du remplacement audio : {e}"})
            return

        await websocket.send_json({
            "type": "progress", "step": "video_merge", "step_number": 4,
            "total_steps": total_steps, "message": "Vidéo doublée générée ✓", "progress": 100,
        })

    # --- Done ---
    result_data = {"dubbed_audio_path": dubbed_audio_path, "segment_count": segment_count}
    if dubbed_video_path:
        result_data["dubbed_video_path"] = dubbed_video_path

    await websocket.send_json({
        "type": "complete", "step": "done",
        "message": "Doublage français généré avec succès !",
        "data": result_data,
    })


def parse_srt_file(srt_path: str) -> tuple[list[dict], list[str]]:
    """Parse an SRT file to extract segments and texts."""
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r'\n\s*\n', content.strip())
    segments = []
    texts = []

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        timestamp_line = None
        timestamp_idx = None
        for i, line in enumerate(lines):
            if '-->' in line:
                timestamp_line = line
                timestamp_idx = i
                break

        if timestamp_line is None:
            continue

        match = re.match(
            r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
            timestamp_line,
        )
        if not match:
            continue

        start = (
            int(match.group(1)) * 3600
            + int(match.group(2)) * 60
            + int(match.group(3))
            + int(match.group(4)) / 1000
        )
        end = (
            int(match.group(5)) * 3600
            + int(match.group(6)) * 60
            + int(match.group(7))
            + int(match.group(8)) / 1000
        )

        text = '\n'.join(lines[timestamp_idx + 1:]).strip()

        segments.append({"index": len(segments), "start": start, "end": end})
        texts.append(text)

    return segments, texts


def get_video_duration(video_path: str) -> float:
    """Get the duration of a video file using ffprobe."""
    import subprocess

    ffprobe_path = settings.get_ffmpeg_path().replace("ffmpeg", "ffprobe")
    if not os.path.isfile(ffprobe_path):
        ffprobe_path = "ffprobe"

    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0