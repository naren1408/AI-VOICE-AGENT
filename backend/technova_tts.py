"""
TechNova Solutions — Text to Speech
Uses Edge-TTS (Microsoft Neural Voices) — completely free, no API key required.
"""
import asyncio
import os
import tempfile
from typing import Optional

# Voice mapping by language code
VOICE_MAP = {
    "en": "en-US-JennyNeural",
    "hi": "hi-IN-SwaraNeural",
    "default": "en-US-JennyNeural",
}


async def _synthesize(text: str, voice: str, output_path: str) -> str:
    """Async TTS synthesis using edge-tts."""
    import edge_tts
    # Strip markdown formatting for cleaner speech
    clean = text.replace("**", "").replace("*", "").replace("#", "").replace("- ", "").strip()
    communicate = edge_tts.Communicate(clean or "Hello! How can I help you today?", voice)
    await communicate.save(output_path)
    return output_path


def speak(text: str, language: str = "en") -> Optional[str]:
    """
    Convert text to speech and return the path to the generated audio file.
    Returns None if TTS fails.
    """
    voice = VOICE_MAP.get(language[:2], VOICE_MAP["default"])
    output_path = os.path.join(tempfile.gettempdir(), "tn_tts_response.mp3")

    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, _synthesize(text, voice, output_path)).result()
            else:
                loop.run_until_complete(_synthesize(text, voice, output_path))
        except RuntimeError:
            asyncio.run(_synthesize(text, voice, output_path))
        return output_path
    except Exception as e:
        print(f"TTS error: {e}")
        return None
