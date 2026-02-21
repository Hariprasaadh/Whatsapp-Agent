import asyncio
import tempfile
import os

import edge_tts


class TextToSpeechError(Exception):
    """Raised when text-to-speech conversion fails."""


class TextToSpeech:
    """Convert text to speech using Microsoft Edge TTS (free, no API key)."""

    VOICE = "en-US-AriaNeural"

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech and return MP3 bytes.

        Raises:
            ValueError:        If text is empty or too long.
            TextToSpeechError: If synthesis fails.
        """
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        if len(text) > 5000:
            raise ValueError("Input text exceeds maximum length of 5000 characters")

        try:
            communicate = edge_tts.Communicate(text, self.VOICE)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                await communicate.save(tmp_path)
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()
            finally:
                os.unlink(tmp_path)

            if not audio_bytes:
                raise TextToSpeechError("Generated audio is empty")

            return audio_bytes

        except TextToSpeechError:
            raise
        except Exception as e:
            raise TextToSpeechError(f"Text-to-speech conversion failed: {str(e)}") from e
