# System Architecture — ElectroMart India Autonomous AI Sales Voice Agent

## High-Level System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Layer (Streamlit Dashboard :8502)"]
        UI["🖥️ Streamlit Multi-Tab UI\n(Live Sales Call, Products & CRM, Sales BI)"]
        AudioInput["🎙️ Microphone / Browser Audio Input"]
        AudioPlayer["🔊 Edge-TTS Player (English, Telugu, Kannada)"]
    end

    subgraph APILayer["API Gateway (FastAPI :8000)"]
        FastAPI["⚡ FastAPI Server (:8000)\nEndpoints: /chat, /products, /leads, /appointments, /health"]
    end

    subgraph VoicePipeline["Voice & Language Processing"]
        STT["🎤 Dual-Engine STT\n(Gemini Live STT / SpeechRecognition)"]
        TTS["🗣️ Text-to-Speech\n(Edge-TTS: Neerja, Shruti, Sapna)"]
    end

    subgraph CoreAgent["AI Sales Agent Engine"]
        Agent["🤖 Sales Agent Orchestrator (Anya)\nContext & 10-Turn Memory"]
        LLM["🧠 LLM Engine\n(Gemini 2.5 Flash / Demo Mode Rule Engine)"]
        RAG["📚 TF-IDF RAG Engine\n(Cosine Similarity on ElectroMart KB)"]
        Sentiment["📊 Sentiment Analyzer\n(Score: -1.0 to +1.0 & Escalation)"]
        LeadScoring["🎯 Lead Qualification Engine\n(BANT Scoring 0-100 & Hot/Warm/Cold)"]
        ApptBooking["📅 Showroom Appointment Engine\n(Slot Validation & .ics Calendar Invite)"]
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
    Agent --> ApptBooking

    ApptBooking --> DB
    LeadScoring --> DB
    Sentiment --> DB
    Agent --> DB

    Agent --> TTS
    TTS --> AudioPlayer
    Agent --> FastAPI
    FastAPI --> UI

    ApptBooking --> Webhook
```

---

## 15-Step End-to-End Processing Workflow

1. **User Input:** Customer speaks into the browser microphone or types in chat (English, Telugu, Kannada).
2. **Audio Capture:** Streamlit captures `.wav` audio binary from `st.audio_input`.
3. **STT Transcription:** `backend/speech_to_text.py` converts speech to text via Gemini STT or Free SpeechRecognition.
4. **API Transmission:** Streamlit transmits user query to FastAPI `/chat` or invokes `execute_sales_turn()`.
5. **Context Retrieval (RAG):** `backend/rag.py` runs TF-IDF vectorization and retrieves top-3 matching chunks from the 8 ElectroMart knowledge base files.
6. **Sentiment Analysis:** `backend/sentiment.py` evaluates turn sentiment (-1.0 to 1.0) and detects escalation flags.
7. **Lead Extraction:** `backend/lead_qualification.py` extracts validated entities (Name, Email, Phone, City, Category, Budget, Timeline).
8. **Lead Qualification:** Computes 0-100 BANT score and classifies lead status (`HOT`, `WARM`, `COLD`).
9. **Agent Reasoning:** LLM (Gemini 2.5 Flash if key present, else intelligent Demo Mode) generates contextual electronics consultation reply.
10. **Appointment Detection:** If the customer asks to visit the showroom, `backend/appointment.py` checks business hours (10 AM - 8:30 PM), prevents duplicate bookings, and generates an `.ics` calendar file.
11. **TTS Synthesis:** `backend/text_to_speech.py` invokes Edge-TTS to produce natural speech in English (`Neerja`), Telugu (`Shruti`), or Kannada (`Sapna`).
12. **Database Persistence:** Messages, call sessions, lead attributes, and catalog recommendations are committed to SQLite (`electromart.db`).
13. **Audio Playback:** Streamlit UI displays agent response and autoplays synthesized speech audio.
14. **Live Dashboard Update:** Live intelligence card, BANT score bar, sentiment trajectory chart, and catalog cards update dynamically.
15. **Call Summary & BI Sync:** At call termination, executive call summary is generated and committed to the CRM dashboard.
