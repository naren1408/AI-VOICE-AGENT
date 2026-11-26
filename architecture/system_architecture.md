# System Architecture — ElectroMart India Autonomous AI Sales Voice Agent

## High-Level System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Layer (Streamlit Dashboard :8502)"]
        UI["🖥️ Streamlit SaaS UI\n(7 Views: Home, Voice Agent, Appointments, CRM, Catalog, BI, Settings)"]
        AudioInput["🎙️ Microphone / Browser Audio Input"]
        AudioPlayer["🔊 Edge-TTS Player (English, Telugu, Kannada, Hindi)"]
    end

    subgraph APILayer["API Gateway (FastAPI :8000)"]
        FastAPI["⚡ FastAPI Server (:8000)\nEndpoints: /chat, /products, /leads, /appointments, /health"]
    end

    subgraph VoicePipeline["Voice & Language Processing"]
        STT["🎤 Dual-Engine STT\n(OpenAI Whisper / Free SpeechRecognition)"]
        TTS["🗣️ Text-to-Speech\n(Edge-TTS: Neerja, Shruti, Sapna, Swara)"]
    end

    subgraph CoreAgent["AI Sales Agent Engine"]
        Agent["🤖 Sales Agent Orchestrator (Anya)\nContext & 10-Turn Memory"]
        LLM["🧠 LLM Engine\n(OpenAI GPT-4o-mini / Demo Mode Rule Engine)"]
        RAG["📚 TF-IDF RAG Engine\n(Cosine Similarity on ElectroMart KB)"]
        Sentiment["📊 Sentiment Analyzer\n(Score: -1.0 to +1.0 & Escalation)"]
        LeadScoring["🎯 Lead Qualification Engine\n(BANT Scoring 0-100 & Hot/Warm/Cold)"]
        ApptBooking["📅 Dual Appointment Engine\n(Manual Portal & 5-Step Voice Flow)"]
    end

    subgraph StorageLayer["Data & Persistence Layer"]
        DB[(🗄️ SQLite Database\nelectromart.db)]
        KBFile["📄 Knowledge Base\n(8 ElectroMart Retail Docs)"]
        CatalogFile["📦 Product Catalog\n(data/products.csv - 25 items)"]
    end

    subgraph Integrations["Calendar & Reporting Layer"]
        ICS["📅 ICS Calendar Generator\n(Outlook / Google Calendar)"]
        Summary["📋 Call Summarizer\n(Lead & Opportunity Extraction)"]
    end

    %% Data Flow
    AudioInput --> STT
    STT --> UI
    UI --> FastAPI
    FastAPI --> Agent

    Agent --> RAG
    RAG <--> KBFile
    Agent --> CatalogFile
    Agent --> LLM
    Agent --> Sentiment
    Agent --> LeadScoring
    Agent --> ApptBooking

    ApptBooking --> DB
    ApptBooking --> ICS
    Agent --> Summary
    Summary --> DB
    LeadScoring --> DB

    Agent --> TTS
    TTS --> AudioPlayer
    Agent --> UI
```

---

## 15-Step End-to-End Processing Workflow

1. **User Input:** Customer speaks into the browser microphone or types in chat (English, Telugu, Kannada, Hindi).
2. **Audio Capture:** Streamlit captures `.wav` audio binary from `st.audio_input`.
3. **STT Transcription:** `backend/speech_to_text.py` converts speech to text via OpenAI Whisper API or Free SpeechRecognition across 4 languages.
4. **API Transmission:** Streamlit transmits user query to FastAPI `/chat` or invokes `execute_sales_turn()`.
5. **Context Retrieval (RAG):** `backend/rag.py` runs TF-IDF vectorization and retrieves top-3 matching chunks from the 8 ElectroMart knowledge base files.
6. **Sentiment Analysis:** `backend/sentiment.py` evaluates turn sentiment (-1.0 to 1.0) and detects escalation flags.
7. **Lead Extraction:** `backend/lead_qualification.py` extracts validated entities (Name, Email, Phone, City, Category, Budget, Timeline).
8. **Lead Qualification:** Computes 0-100 BANT score and classifies lead status (`HOT`, `WARM`, `COLD`).
9. **Agent Reasoning:** LLM (OpenAI GPT-4o-mini if key present, else intelligent Demo Mode) generates contextual electronics consultation reply or directly answers product specs.
10. **Dual Appointment Booking:** Via conversational 5-step flow or dedicated manual booking portal with past-date checks, business hours validation (10 AM - 8:30 PM), duplicate booking lock, and RFC 5545 `.ics` calendar generation.
11. **TTS Synthesis:** `backend/text_to_speech.py` invokes Edge-TTS to produce natural speech in English (`Neerja`), Telugu (`Shruti`), Kannada (`Sapna`), or Hindi (`Swara`).
12. **Database Persistence:** Messages, call sessions, lead attributes, and catalog recommendations are committed to SQLite (`electromart.db`).
13. **Audio Playback:** Streamlit UI displays agent response and autoplays synthesized speech audio.
14. **Live Dashboard Update:** Live intelligence card, BANT score bar, sentiment trajectory chart, and catalog cards update dynamically.
15. **Call Summary & BI Sync:** At call termination, executive call summary is generated and committed to the CRM dashboard.
