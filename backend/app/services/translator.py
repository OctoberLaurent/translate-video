"""Translation service using LM Studio local API."""
import asyncio
import logging
import re
from typing import Callable

import httpx

from app.utils.config import settings

logger = logging.getLogger(__name__)


class TranslatorService:
    """Handle translation of text segments via LM Studio API."""

    def __init__(self, model: str | None = None, port: int | None = None, custom_prompt: str | None = None):
        """
        Initialize translator service.

        Args:
            model: LM Studio model identifier. If None, uses first available.
            port: LM Studio server port. If None, uses default from settings.
            custom_prompt: Optional custom instruction to prepend to the system prompt.
        """
        if port:
            self.base_url = f"http://localhost:{port}/v1"
        else:
            self.base_url = settings.LM_STUDIO_BASE_URL
        self.timeout = settings.LM_STUDIO_TIMEOUT
        self.model = model
        self.chunk_size = settings.TRANSLATION_CHUNK_SIZE
        self.temperature = settings.TRANSLATION_TEMPERATURE
        if custom_prompt:
            self.system_prompt = settings.TRANSLATION_SYSTEM_PROMPT + "\n\nAdditional instructions: " + custom_prompt
        else:
            self.system_prompt = settings.TRANSLATION_SYSTEM_PROMPT

    async def get_available_models(self) -> list[dict]:
        """
        Fetch available models from LM Studio.

        Returns:
            List of model objects with 'id' and other metadata.

        Raises:
            ConnectionError: If LM Studio is not reachable.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/models")
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except httpx.ConnectError:
            raise ConnectionError(
                "Impossible de se connecter à LM Studio. "
                "Vérifiez que LM Studio est lancé avec le serveur local activé sur le port 1234."
            )
        except httpx.TimeoutException:
            raise ConnectionError("LM Studio ne répond pas (timeout).")

    async def translate_segments(
        self,
        segments: list[dict],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[str]:
        """
        Translate a list of text segments from English to French via LM Studio.

        Segments are processed in chunks to avoid context window overflow.

        Args:
            segments: List of dicts with 'index', 'start', 'end', 'text' keys.
            progress_callback: Optional callback(chunk_index, total_chunks) for progress.

        Returns:
            List of translated text strings, in the same order as input.
        """
        if not segments:
            return []

        # If model not specified, try to get the first available one
        if self.model is None:
            models = await self.get_available_models()
            if models:
                self.model = models[0]["id"]
            else:
                raise RuntimeError("Aucun modèle LLM disponible dans LM Studio.")

        # Split segments into chunks
        chunks = self._create_chunks(segments)
        total_chunks = len(chunks)
        translated_texts = [""] * len(segments)

        logger.info(
            f"Starting translation: {len(segments)} segments in {total_chunks} chunks"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for chunk_idx, chunk in enumerate(chunks):
                # Build the text to translate
                chunk_text = "\n".join(
                    f"[{s['index']}] {s['text']}" for s in chunk
                )

                translated = await self._translate_chunk(client, chunk_text)

                # Parse translated lines back to individual segments
                translated_lines = self._parse_translated_lines(
                    translated, len(chunk)
                )

                # Map back to original indices
                for i, segment in enumerate(chunk):
                    orig_idx = segment["index"]
                    if i < len(translated_lines):
                        translated_texts[orig_idx] = translated_lines[i]
                    else:
                        # Fallback: keep original text
                        translated_texts[orig_idx] = segment["text"]

                if progress_callback:
                    progress_callback(chunk_idx + 1, total_chunks)

                logger.info(
                    f"Translated chunk {chunk_idx + 1}/{total_chunks} "
                    f"({len(chunk)} segments)"
                )

        return translated_texts

    async def _translate_chunk(
        self, client: httpx.AsyncClient, text: str
    ) -> str:
        """
        Send a single translation request to LM Studio.

        Args:
            client: HTTP client instance.
            text: Text to translate.

        Returns:
            Translated text string.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": self.temperature,
            "max_tokens": 4096,
        }

        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            response.raise_for_status()

            result = response.json()
            translated = result["choices"][0]["message"]["content"]

            return self._clean_translation(translated)

        except httpx.ConnectError:
            raise ConnectionError(
                "Connexion perdue avec LM Studio pendant la traduction."
            )
        except httpx.TimeoutException:
            raise ConnectionError(
                "LM Studio a mis trop de temps à répondre (timeout). "
                "Essayez avec un modèle plus léger ou des chunks plus petits."
            )
        except KeyError as e:
            raise RuntimeError(f"Réponse inattendue de LM Studio: {e}")

    def _create_chunks(
        self, segments: list[dict]
    ) -> list[list[dict]]:
        """Split segments into chunks of configured size."""
        chunks = []
        for i in range(0, len(segments), self.chunk_size):
            chunks.append(segments[i : i + self.chunk_size])
        return chunks

    @staticmethod
    def _clean_translation(text: str) -> str:
        """
        Clean the LLM translation output.
        Remove unwanted prefixes, commentary, and formatting artifacts.
        """
        # Remove common LLM preamble patterns
        text = re.sub(
            r"^(Here is the translation|Voici la traduction|Translation|Traduction)\s*[:：]\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )
        # Remove markdown formatting
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"[*_#`]", "", text)
        # Remove surrounding quotes
        text = text.strip().strip('"').strip("'").strip()
        # Remove any standalone [N] prefixes that may appear on lines
        text = re.sub(r"(?m)^\[\d+\]\s*", "", text)
        return text

    @staticmethod
    def _parse_translated_lines(translated: str, expected_count: int) -> list[str]:
        """
        Parse the translated text back into individual lines.
        
        Try to match indexed format first, then fall back to line-by-line.
        """
        # Try indexed format: [0] Translated text
        indexed_pattern = re.compile(r"\[(\d+)\]\s*(.*)")
        indexed_matches = indexed_pattern.findall(translated)

        if indexed_matches and len(indexed_matches) == expected_count:
            return [match[1].strip() for match in indexed_matches]

        # Fallback: split by newlines and strip any [N] prefixes
        lines = [re.sub(r"^\[\d+\]\s*", "", line).strip() for line in translated.split("\n") if line.strip()]

        # If we got the right number of lines, use them
        if len(lines) == expected_count:
            return lines

        # If we got fewer lines, pad with empty strings
        if len(lines) < expected_count:
            return lines + [""] * (expected_count - len(lines))

        # If we got more lines, merge extras (LLM sometimes splits lines)
        result = []
        idx = 0
        for i in range(expected_count):
            if i == expected_count - 1:
                result.append(" ".join(lines[idx:]))
            else:
                if idx < len(lines):
                    result.append(lines[idx])
                    idx += 1
                else:
                    result.append("")
        return result