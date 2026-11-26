"""
ElectroMart India — Central Configuration
All model names, voice mappings, and business constants in one file for quick live-demo changes.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- BUSINESS IDENTITY ---
COMPANY_NAME = "ElectroMart India"
AGENT_NAME = "Anya"
AGENT_TITLE = "ElectroMart India AI Sales Advisor"
AGENT_ROLE_DESCRIPTION = (
    "You are Anya, ElectroMart India's professional AI Sales Assistant. "
    "Help customers choose electronics (laptops, smartphones, tablets, accessories) "
    "based on their exact needs, budget, and preferences."
)

# --- AI & MODEL CONFIGURATION ---
# Central location to change model name or endpoint during live interview demo
OPENAI_MODEL_CHAT = os.getenv("OPENAI_MODEL_CHAT", "gpt-4o-mini")
OPENAI_MODEL_STT = os.getenv("OPENAI_MODEL_STT", "whisper-1")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)  # Compatible with Groq, DeepSeek, Ollama, OpenRouter
MAX_HISTORY_TURNS = 10

# --- TTS NEURAL VOICE MAPPING ---
# Natural Edge-TTS Microsoft Neural voices for supported languages: English, Telugu, Kannada, Hindi
TTS_VOICES = {
    "en": "en-IN-NeerjaNeural",     # Indian English natural female voice
    "en-US": "en-US-JennyNeural",   # US English
    "te": "te-IN-ShrutiNeural",     # Telugu natural female voice
    "kn": "kn-IN-SapnaNeural",      # Kannada natural female voice
    "hi": "hi-IN-SwaraNeural",      # Hindi natural female voice
    "default": "en-IN-NeerjaNeural"
}

# --- BUSINESS RULES ---
STORE_HOURS_START = 10  # 10:00 AM
STORE_HOURS_END = 20    # 08:30 PM (20:30)
SHOWROOM_CITIES = [
    "Mumbai", "Bengaluru", "New Delhi", "Hyderabad",
    "Pune", "Ahmedabad", "Kolkata", "Chennai"
]
