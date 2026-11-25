# CloudScale AI: Autonomous Sales Voice Agent MVP

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Google GenAI](https://img.shields.io/badge/Google_GenAI-Gemini_2.5_Flash-4285F4.svg?style=flat&logo=google)](https://ai.google.dev/)
[![Edge-TTS](https://img.shields.io/badge/Edge--TTS-Neural_Voices-0078D7.svg?style=flat)](https://github.com/rany2/edge-tts)
[![SQLite](https://img.shields.io/badge/Database-SQLite_SQLAlchemy-003B57.svg?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)

An autonomous, multilingual B2B Sales Voice Agent built for a senior AI engineering hiring challenge. The agent speaks with inbound prospects, answers questions strictly from the company knowledge base using RAG, qualifies leads (0-100 score + HOT/WARM/COLD), prevents calendar double-booking with atomic database transactions, logs appointments, and syncs summaries with downstream CRMs.

---

## Architecture

![System Architecture](architecture/system_architecture.png)

```
[Customer Browser / Mic] 
         │ (Audio/Text)
         ▼
[Streamlit UI / FastAPI Gateway]
         │
    ┌────┴───────────────────────────┐
    ▼                                ▼
[Gemini STT]                 [Simple RAG Engine]
(gemini-2.5-flash)           (company_info.txt + Embeddings)
    │                                │
    └──────────────┬─────────────────┘
                   ▼
         [Ava: Autonomous Agent] ──▶ [Lead Qualification (0-100)]
         (Gemini 2.5 Flash / Demo) ──▶ [Sentiment Analysis (-1 to 1)]
                   │
    ┌──────────────┴─────────────────┐
    ▼                                ▼
[Edge-TTS Neural Audio]      [Transactional Booking & CRM]
(en-US-Jenny / hi-IN-Swara)  (SQLite + .ics + Webhook)
```

---

## Feature Status Table

| Feature | Category | Implementation Details |
| :--- | :--- | :--- |
| **Multilingual Voice & Text Chat** | **Working** | Streamlit UI + Edge-TTS neural speech in English and Hindi. |
| **STT Voice Transcription** | **Working** (Gemini) / **Demo Mode** | Uses `gemini-2.5-flash` with audio prompt when key is present; fallback to text in Demo Mode. |
| **Company RAG Retrieval** | **Working** | Cosine similarity over `company_info.txt` via Gemini embeddings; keyword overlap fallback. |
| **Lead Qualification & Scoring** | **Working** | 0-100 deterministic scoring (Budget, Timeline, Decision Maker, Need, Contact); HOT/WARM/COLD tags. |
| **Live Sentiment & Escalation** | **Working** | Turn-by-turn sentiment scoring (-1.0 to +1.0) with real-time UI line chart and human escalation banner. |
| **Transactional Demo Booking** | **Working** | Real-time business day & hour validation, SQLite conflict prevention lock, and `.ics` download. |
| **CRM Webhook & SQLite CRM** | **Working** | Upserts leads by call ID/email; POSTs JSON payloads to `/crm/webhook` (HubSpot/Zoho simulation). |
| **Call Summary & Insights** | **Working** | Structured summary generation, conversion rates, average score, and sentiment pie chart. |
| **Zero-Key Demo Mode** | **Demo Mode** | Complete sales flow operates seamlessly without external API keys. |
| **Telephony (Twilio / Exotel)** | **Future enhancement** | SIP trunking and WebRTC gateway architecture documented in project report. |
| **100,000 Concurrent Calls** | **Future enhancement** | Scalability design plan detailed in `reports/project_report.md` (stateless pods, Celery, Redis, Qdrant). |

---

## Quickstart & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.11)
- Git

### 2. Installation
```bash
# Clone or navigate to the repository
cd "f:\AI VOICE AGENT"

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example configuration
cp .env.example .env
```
* **To run in Gemini AI Mode**: Add your key to `.env`:
  ```ini
  GEMINI_API_KEY=your_gemini_api_key_here
  ```
* **To run in Demo Mode**: Leave `GEMINI_API_KEY` empty. The app automatically runs offline with full sales qualification.

### 4. Run Application
Open two terminal windows:

* **Terminal 1: Start FastAPI Backend**
  ```bash
  uvicorn backend.main:app --reload --port 8000
  ```

* **Terminal 2: Launch Streamlit UI**
  ```bash
  streamlit run app.py
  ```
Navigate to `http://localhost:8501` in your browser.

---

## 13-Step Demo Walkthrough
Follow the complete script in [`demo_script.md`](file:///f:/AI%20VOICE%20AGENT/demo_script.md):
1. **Pricing Inquiry**: Ask about tiers -> Agent retrieves Starter ($499), Pro ($1,499), Enterprise ($4,500).
2. **Infrastructure Scale**: Tell agent you have 180 nodes on AWS.
3. **Budget & Timeline**: State budget is $1,499/mo needed this quarter -> Score updates to WARM.
4. **Decision Maker**: Introduce yourself as VP of Engineering with email -> Lead updates to 🔥 HOT (100/100).
5. **Hindi Query**: Ask a question in Hindi -> Agent responds in Hindi with neural voice.
6. **Book Demo**: Request a demo for tomorrow 4pm -> Slot is locked; `.ics` invite is downloadable.
7. **End Call**: View structured executive summary and CRM synchronization in Insights tab.

---

## Live-Coding Cheat Sheet (For Interview Live Changes)

| What to Change | File | Exact Variable or Section |
| :--- | :--- | :--- |
| **Gemini Model Name** | [`backend/ai_agent.py`](file:///f:/AI%20VOICE%20AGENT/backend/ai_agent.py) | `GEMINI_MODEL_CHAT = "gemini-2.5-flash"` |
| **System Prompt** | [`backend/ai_agent.py`](file:///f:/AI%20VOICE%20AGENT/backend/ai_agent.py) | `SALES_SYSTEM_PROMPT = """..."""` |
| **Lead Scoring Weights** | [`backend/lead_qualification.py`](file:///f:/AI%20VOICE%20AGENT/backend/lead_qualification.py) | `LEAD_SCORING_WEIGHTS = {...}` |
| **Language & Voice Map** | [`backend/text_to_speech.py`](file:///f:/AI%20VOICE%20AGENT/backend/text_to_speech.py) | `LANGUAGE_VOICE_MAP = {...}` |
| **RAG Chunk Size** | [`backend/rag.py`](file:///f:/AI%20VOICE%20AGENT/backend/rag.py) | `RAG_CHUNK_SIZE_WORDS = 300` |
| **Appointment Hours / Duration**| [`backend/appointment.py`](file:///f:/AI%20VOICE%20AGENT/backend/appointment.py) | `WORK_HOURS_START = 9`, `WORK_HOURS_END = 18` |

---

## Project Structure
```
AI-Sales-Voice-Agent/
├── app.py                      # Streamlit UI with 3 tabs (Live Call, Leads, Insights)
├── requirements.txt            # Modern pinned dependencies
├── .env                        # Environment variables (GEMINI_API_KEY)
├── .env.example
├── .gitignore
├── .streamlit/config.toml      # Polished dark theme
├── backend/
│   ├── main.py                 # FastAPI endpoints & CORS
│   ├── ai_agent.py             # LLM orchestration, system prompt, memory & Demo replies
│   ├── speech_to_text.py       # Gemini STT & language detection
│   ├── text_to_speech.py       # Edge-TTS neural speech synthesis
│   ├── rag.py                  # Chunking, embeddings & cosine similarity retrieval
│   ├── lead_qualification.py   # Pydantic extraction & 0-100 rule scoring
│   ├── sentiment.py            # Turn sentiment (-1 to 1) & human escalation
│   └── appointment.py          # Slot availability, atomic booking & .ics generation
├── database/
│   ├── db.py                   # SQLAlchemy engine & session factory
│   └── models.py               # Lead, Call, Message, Appointment models
├── knowledge_base/
│   └── company_info.txt        # Realistic B2B FinOps company documentation
├── reports/
│   └── project_report.md       # 1-page executive project report
├── architecture/
│   ├── generate_diagram.py     # Clean Matplotlib architecture generator
│   └── system_architecture.png # Generated architecture PNG
├── tests/
│   └── test_core.py            # Comprehensive test suite (scoring, booking, RAG, sentiment)
├── demo_script.md              # Exact demo script utterances (English + Hindi)
├── Dockerfile                  # Container definition
└── README.md
```

---

## TechNova Solutions: AI Sales Voice Agent (7-Page Dashboard)

A comprehensive enterprise sales agent and CRM dashboard for **TechNova Solutions** (CRM, ERP, and Analytics software).

### Key Features
- **7-Page Streamlit Dashboard (`technova_app.py`)**:
  1. 📊 **Dashboard:** Real-time metrics, lead breakdown pie chart, sentiment distribution bar chart, recent leads table, upcoming demos.
  2. 🤖 **AI Voice Agent:** Interactive chat with live lead card, sentiment trajectory chart, voice input, Edge-TTS audio playback, and call summary generator.
  3. 👥 **Lead Management:** Filterable, searchable CRM table with manual status override.
  4. 📅 **Appointments:** Booking form with conflict checks, scheduled appointments list, and status updates.
  5. 📚 **Knowledge Base:** View knowledge base content, test RAG retrieval, and upload additional documents (.txt, .md).
  6. 📋 **Call Reports:** Detailed summaries with customer requirements, sentiment tags, and next actions.
  7. ⚙️ **Settings:** API status, agent configuration, and one-click demo data re-seeding.
- **FastAPI Backend (`backend/technova_main.py`)**: REST endpoints for `/health`, `/chat`, `/leads`, `/appointments`, `/reports`, `/crm/webhook`.
- **Zero-Key Demo Mode**: Fully functional with smart keyword matching and TF-IDF RAG retrieval over `knowledge_base/technova_info.txt`. Optionally switch to OpenAI GPT by providing `OPENAI_API_KEY`.
- **Pre-Seeded Data**: Never opens with empty charts — automatically populates with realistic B2B leads, appointments, and reports on first run.

### Running TechNova Solutions

```bash
# Terminal 1: Launch TechNova FastAPI Backend (Port 8001)
python -m uvicorn backend.technova_main:app --port 8001 --reload

# Terminal 2: Launch TechNova Streamlit Dashboard (Port 8503)
python -m streamlit run technova_app.py --server.port 8503
```
Open **http://localhost:8503** in your browser.

---

## Running Tests
Run the automated test suite verifying lead qualification, slot conflict handling, sentiment parsing, and RAG retrieval:
```bash
python -m pytest tests/ -v
```
