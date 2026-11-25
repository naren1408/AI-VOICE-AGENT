import os
import asyncio
import edge_tts

# --- LANGUAGE TO VOICE MAPPING (Single dictionary for easy live-coding & demo) ---
LANGUAGE_VOICE_MAP = {
    "en": "en-US-JennyNeural",     # High quality natural English (US)
    "hi": "hi-IN-SwaraNeural",     # High quality natural Hindi (IN)
    "default": "en-US-JennyNeural"
}


async def generate_speech_async(text: str, output_path: str, language: str = "en") -> str:
    """Generate speech audio file from text using edge-tts (free, no API key required)."""
    clean_lang = language.lower()[:2] if language else "en"
    voice = LANGUAGE_VOICE_MAP.get(clean_lang, LANGUAGE_VOICE_MAP["default"])

    # Ensure output folder exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Clean text of markdown formatting for clear spoken output
    spoken_text = text.replace("**", "").replace("#", "").replace("- ", "").strip()
    if not spoken_text:
        spoken_text = "I am ready to help you."

    communicate = edge_tts.Communicate(spoken_text, voice)
    await communicate.save(output_path)
    return output_path


def text_to_speech(text: str, output_path: str, language: str = "en") -> str:
    """Synchronous wrapper for edge-tts generation."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If running in an event loop (e.g. FastAPI / Jupyter)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(asyncio.run, generate_speech_async(text, output_path, language)).result()
        else:
            loop.run_until_complete(generate_speech_async(text, output_path, language))
    except RuntimeError:
        asyncio.run(generate_speech_async(text, output_path, language))
    return output_path
