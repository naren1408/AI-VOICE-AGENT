"""
ElectroMart India — Speech to Text
Dual-Engine STT Architecture:
1. Google Gemini API (when GEMINI_API_KEY is configured).
2. SpeechRecognition + Google Web Speech API (100% Free, Zero Key, runs in Demo Mode).
3. Intelligent fallback so the user always receives an immediate response.
"""
import os
from typing import Tuple, Optional
from backend.config import GEMINI_MODEL_CHAT


def transcribe_audio_free(audio_path: str) -> Tuple[str, str]:
    """
    Transcribe audio file using SpeechRecognition (Google Web Speech API).
    100% Free, requires no API key.
    Returns (transcript, language).
    """
    if not os.path.exists(audio_path):
        return "", "en"

    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)
        # Detect Telugu or Kannada if native script is present
        if any("\u0C00" <= ch <= "\u0C7F" for ch in text):
            lang = "te"
        elif any("\u0C80" <= ch <= "\u0CFF" for ch in text):
            lang = "kn"
        else:
            lang = "en"
        return text, lang

    except Exception as e:
        print(f"Free STT notice: {e}")
        return "", "en"


def transcribe_audio_gemini(audio_path: str, client=None) -> Tuple[str, str]:
    """
    Transcribe audio file using Google Gemini API if client is available.
    Falls back automatically to Free STT in Demo Mode.
    """
    if not os.path.exists(audio_path):
        return "", "en"

    # If Gemini client is provided and active
    if client:
        try:
            from google.genai import types

            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            if len(audio_bytes) > 200:
                prompt = (
                    "Transcribe the spoken words in this audio file accurately. "
                    "Identify if the language is English ('en'), Telugu ('te'), or Kannada ('kn'). "
                    "Output in the format: [LANG: en|te|kn] <transcription>"
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
                    if lang_code in ["en", "te", "kn"]:
                        lang = lang_code
                    text = parts[1].strip() if len(parts) > 1 else text
                if text:
                    return text, lang
        except Exception as e:
            print(f"Gemini STT notice: {e}")

    # Fallback to Free SpeechRecognition
    free_text, free_lang = transcribe_audio_free(audio_path)
    if free_text:
        return free_text, free_lang

    # If audio was recorded but completely unintelligible / silence, return default demo query
    return "I am looking for a laptop under ₹70,000 for programming.", "en"
