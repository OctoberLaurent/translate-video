"""Pipeline router — orchestrate the full subtitle generation process."""
import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.services.audio_extractor import AudioExtractor
from app.services.whisper_service import WhisperService
from app.services.translator import TranslatorService
from app.services.srt_builder import SRTBuilder
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
    
    Receives configuration and sends real-time progress updates.
    
    Expected message format:
    {
        "file_path": "/path/to/video.mp4",
        "whisper_model": "base",
        "llm_model": "model-id",
        "whisper_task": "translate"  // "translate" or "transcribe"
    }
    """
    await manager.connect(websocket)
    
    try:
        # Wait for configuration message
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

        await run_pipeline(websocket, file_path, whisper_model, llm_model, whisper_task, lm_studio_port, translation_prompt)

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
    """Execute the full 4-step pipeline with progress updates."""

    # --- Step 1: Audio Extraction ---
    await websocket.send_json({
        "type": "progress",
        "step": "extraction",
        "step_number": 1,
        "total_steps": 4,
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
        "total_steps": 4,
        "message": "Audio extrait avec succès ✓",
        "progress": 100,
    })

    # --- Step 2: Whisper Transcription ---
    await websocket.send_json({
        "type": "progress",
        "step": "transcription",
        "step_number": 2,
        "total_steps": 4,
        "message": f"Transcription avec Whisper ({whisper_model}) en cours...",
        "progress": 0,
    })

    try:
        whisper = WhisperService(model_size=whisper_model)
        loop = asyncio.get_event_loop()

        # Thread-safe progress callback for Whisper transcription
        def on_whisper_progress(pct: int, message: str):
            """Send Whisper progress from the executor thread via WebSocket."""
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({
                    "type": "progress",
                    "step": "transcription",
                    "step_number": 2,
                    "total_steps": 4,
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
        "total_steps": 4,
        "message": f"Transcription terminée ✓ ({segment_count} segments, langue: {result.detected_language})",
        "progress": 100,
        "data": {
            "segment_count": segment_count,
            "detected_language": result.detected_language,
            "duration": result.duration,
        },
    })

    # Prepare segments for translation
    segments = [
        {
            "index": s.index,
            "start": s.start,
            "end": s.end,
            "text": s.text,
        }
        for s in result.segments
    ]

    # Unload whisper to free memory
    whisper.unload_model()

    # --- Step 3: Translation via LM Studio ---
    await websocket.send_json({
        "type": "progress",
        "step": "translation",
        "step_number": 3,
        "total_steps": 4,
        "message": "Traduction en cours via LM Studio...",
        "progress": 0,
    })

    def on_translation_progress(current: int, total: int):
        """Send translation progress updates (sync callback)."""
        pass  # Progress is sent from the async loop below

    try:
        translator = TranslatorService(model=llm_model, port=lm_studio_port, custom_prompt=translation_prompt)

        # Translate with chunked progress
        chunks = translator._create_chunks(segments)
        total_chunks = len(chunks)
        translated_texts = [""] * len(segments)

        async with __import__("httpx").AsyncClient(timeout=translator.timeout) as client:
            for chunk_idx, chunk in enumerate(chunks):
                chunk_text = "\n".join(
                    f"[{s['index']}] {s['text']}" for s in chunk
                )

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
                    "total_steps": 4,
                    "message": f"Traduction : bloc {chunk_idx + 1}/{total_chunks}",
                    "progress": progress_pct,
                })

    except ConnectionError as e:
        await websocket.send_json({
            "type": "error",
            "step": "translation",
            "message": str(e),
        })
        return
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "step": "translation",
            "message": f"Erreur lors de la traduction : {e}",
        })
        return

    await websocket.send_json({
        "type": "progress",
        "step": "translation",
        "step_number": 3,
        "total_steps": 4,
        "message": "Traduction terminée ✓",
        "progress": 100,
    })

    # --- Step 4: SRT Assembly ---
    await websocket.send_json({
        "type": "progress",
        "step": "srt",
        "step_number": 4,
        "total_steps": 4,
        "message": "Assemblage du fichier SRT...",
        "progress": 0,
    })

    try:
        srt_path = SRTBuilder.generate_output_path(file_path, settings.OUTPUT_DIR)
        SRTBuilder.build_srt(segments, translated_texts, srt_path)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "step": "srt",
            "message": f"Erreur lors de l'assemblage SRT : {e}",
        })
        return

    await websocket.send_json({
        "type": "progress",
        "step": "srt",
        "step_number": 4,
        "total_steps": 4,
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
        },
    })