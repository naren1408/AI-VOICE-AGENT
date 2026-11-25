"""
ElectroMart India — Speech to Text
Uses Google Gemini API (current google-genai SDK) when configured.
Falls back gracefully when running offline in Demo Mode.
"""
import os
from typing import Tuple, Optional
from backend.config import GEMINI_MODEL_CHAT


def transcribe_audio_gemini(audio_path: str, client=None) -> Tuple[str, str]:
    """
    Transcribe audio file using Google Gemini API.
    Returns (transcript_text, detected_language).
    """
    if not client or not os.path.exists(audio_path):
        return "", "en"

    try:
        from google.genai import types

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        if len(audio_bytes) < 100:
            return "", "en"

        prompt = (
            "Listen to this customer voice recording. Transcribe the exact words spoken. "
            "Also identify if the speech is in English ('en') or Hindi ('hi'). "
            "Output strictly formatted as: [LANG: en|hi] <transcription>"
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL_CHAT,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                prompt
            ]
        )

        text = response.text.strip()
        lang = "en"
        if text.startswith("[LANG:"):
            parts = text.split("]", 1)
            lang_code = parts[0].replace("[LANG:", "").strip().lower()
            if lang_code in ["en", "hi"]:
                lang = lang_code
            text = parts[1].strip() if len(parts) > 1 else text

        return text, lang

    except Exception as e:
        print(f"Gemini STT notice: {e}")
        return f"Audio transcription error: {str(e)[:60]}", "en"
