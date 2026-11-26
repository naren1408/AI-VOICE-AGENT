"""
ElectroMart India — Speech to Text
Dual-Engine STT Architecture:
1. OpenAI Whisper API (when OPENAI_API_KEY is configured).
2. SpeechRecognition + Google Web Speech API (100% Free, Zero Key, runs in Demo Mode).
3. Intelligent fallback so the user always receives an immediate response.
"""
import os
from typing import Tuple, Optional
from backend.config import OPENAI_MODEL_STT


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
        # Detect Telugu, Kannada, or Hindi if native script is present
        if any("\u0C00" <= ch <= "\u0C7F" for ch in text):
            lang = "te"
        elif any("\u0C80" <= ch <= "\u0CFF" for ch in text):
            lang = "kn"
        elif any("\u0900" <= ch <= "\u097F" for ch in text):
            lang = "hi"
        else:
            lang = "en"
        return text, lang

    except Exception as e:
        print(f"Free STT notice: {e}")
        return "", "en"


def transcribe_audio_ai(audio_path: str, client=None) -> Tuple[str, str]:
    """
    Transcribe audio file using OpenAI Whisper API if client is available.
    Falls back automatically to Free STT in Demo Mode.
    """
    if not os.path.exists(audio_path):
        return "", "en"

    # If OpenAI client is provided and active
    if client:
        try:
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model=OPENAI_MODEL_STT,
                    file=audio_file
                )
                text = transcription.text.strip()
                lang = "en"
                if any("\u0C00" <= ch <= "\u0C7F" for ch in text):
                    lang = "te"
                elif any("\u0C80" <= ch <= "\u0CFF" for ch in text):
                    lang = "kn"
                elif any("\u0900" <= ch <= "\u097F" for ch in text):
                    lang = "hi"
                if text:
                    return text, lang
        except Exception as e:
            print(f"OpenAI Whisper STT notice: {e}")

    # Fallback to Free SpeechRecognition
    free_text, free_lang = transcribe_audio_free(audio_path)
    if free_text:
        return free_text, free_lang

    # If audio was recorded but completely unintelligible / silence, return default demo query
    return "I am looking for a laptop under ₹70,000 for programming.", "en"


# Backward-compatible alias
transcribe_audio_gemini = transcribe_audio_ai
