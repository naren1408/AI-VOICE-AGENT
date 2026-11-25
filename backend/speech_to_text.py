import os
from typing import Tuple

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi"]


def detect_language(text: str) -> str:
    """Detect whether language is Hindi or English based on Devanagari script or common transliteration."""
    # Check for Devanagari Unicode block (\u0900 to \u097F)
    for ch in text:
        if "\u0900" <= ch <= "\u097F":
            return "hi"

    # Common Hindi transliterations in sales inquiries
    hindi_keywords = ["namaste", "bataiye", "kya", "daam", "kitna", "keemat", "shukriya", "dhanyawad", "badiya", "hai", "mujhe", "chahiye"]
    text_lower = text.lower()
    if any(re_match in text_lower.split() for re_match in hindi_keywords):
        return "hi"

    return "en"


def transcribe_audio_gemini(audio_path: str, client=None, model_name: str = "gemini-2.5-flash") -> Tuple[str, str]:
    """Transcribe audio using the Gemini API. Returns (transcribed_text, language_code)."""
    if not os.path.exists(audio_path):
        return "No audio file provided.", "en"

    if client is None:
        return "Audio transcription requires a valid GEMINI_API_KEY. Please use text input in Demo Mode.", "en"

    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        prompt = (
            "Listen carefully to this audio recording from an inbound sales inquiry. "
            "Transcribe the spoken audio verbatim in its original language (English or Hindi). "
            "Output ONLY the plain transcription text without any additional commentary."
        )

        response = client.models.generate_content(
            model=model_name,
            contents=[
                prompt,
                {"mime_type": "audio/wav", "data": audio_bytes}
            ]
        )
        transcript = response.text.strip()
        lang = detect_language(transcript)
        return transcript, lang
    except Exception as err:
        return f"Audio transcription error: {str(err)}", "en"
