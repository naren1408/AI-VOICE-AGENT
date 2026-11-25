"""
TechNova Solutions — Speech to Text
Uses browser audio capture (st.audio_input) and SpeechRecognition library.
Falls back gracefully when microphone or internet is unavailable.
"""
import os
import tempfile
from typing import Tuple


def transcribe_audio_file(audio_bytes: bytes) -> Tuple[str, str]:
    """
    Transcribe audio bytes to text using Google Web Speech API (free, no key needed).
    Returns (transcribed_text, status_message).
    Status: 'success', 'unavailable', or 'error'.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        return "", "SpeechRecognition library not installed. Please run: pip install SpeechRecognition"

    recognizer = sr.Recognizer()

    # Write audio bytes to a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with sr.AudioFile(tmp_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.record(source)

        # Google Web Speech API (free, requires internet)
        text = recognizer.recognize_google(audio_data)
        return text, "success"

    except sr.UnknownValueError:
        return "", "Could not understand the audio. Please speak clearly and try again."
    except sr.RequestError as e:
        return "", f"Speech recognition service unavailable: {e}. Please type your message."
    except Exception as e:
        return "", f"Audio processing error: {str(e)}"
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
