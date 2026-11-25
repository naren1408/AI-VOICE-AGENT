"""
ElectroMart India — Text to Speech
Uses Microsoft Edge Neural Voices via edge-tts. Free, high quality natural speech, zero API key.
"""
import os
import uuid
import asyncio
import tempfile
from typing import Optional
from backend.config import TTS_VOICES


async def _synthesize_async(text: str, voice: str, output_path: str) -> str:
    """Run asynchronous TTS generation."""
    import edge_tts
    # Remove markdown asterisks and hashtags for clean, natural speech
    clean = text.replace("**", "").replace("*", "").replace("#", "").replace("- ", "").strip()
    if not clean:
        clean = "Welcome to ElectroMart India. How may I assist you today?"

    communicate = edge_tts.Communicate(clean, voice)
    await communicate.save(output_path)
    return output_path


def text_to_speech(text: str, language: str = "en", output_path: Optional[str] = None) -> Optional[str]:
    """
    Synchronous entry point to convert text into spoken audio MP3.
    Uses unique filename per turn to prevent Windows file-locking conflicts.
    """
    lang_key = language[:2].lower() if language else "en"
    voice = TTS_VOICES.get(lang_key, TTS_VOICES["default"])

    if not output_path:
        temp_dir = os.path.join(tempfile.gettempdir(), "electromart_audio")
        os.makedirs(temp_dir, exist_ok=True)
        output_path = os.path.join(temp_dir, f"speech_{uuid.uuid4().hex[:8]}.mp3")

    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, _synthesize_async(text, voice, output_path)).result()
            else:
                loop.run_until_complete(_synthesize_async(text, voice, output_path))
        except RuntimeError:
            asyncio.run(_synthesize_async(text, voice, output_path))
        return output_path
    except Exception as e:
        print(f"TTS synthesis notice: {e}")
        return None
