# ElectroMart India — Technical Placement Interview Preparation Guide

This guide enables you to explain every file and function in under 60 seconds and ace technical interview discussions.

---

## ⏱️ The 60-Second File & Architecture Elevator Pitch

| File Path | 60-Second Explanation for Interviewer | Key Function / Variable to Show |
| :--- | :--- | :--- |
| `app.py` | **Streamlit SaaS Dashboard:** Modern FinBank-inspired layout featuring a consistent left navigation sidebar across 7 views (Home Dashboard, AI Voice Assistance, Appointments & Booking, CRM & Leads, Knowledge Base & Catalog, Business Insights, Settings) and live CRM counters. | `selected_nav = st.radio(...)`, `execute_sales_turn(...)` |
| `backend/main.py` | **FastAPI REST API:** Exposes production endpoints for `/health`, `/call/start`, `/call/{id}/text`, `/call/{id}/audio`, `/products`, `/leads`, `/appointments`, and `/insights`. Uses Pydantic schemas and CORS middleware. | `handle_text_turn(...)`, `handle_audio_turn(...)` |
| `backend/config.py` | **Central Configuration:** Houses business constants, agent identity, Edge-TTS voice mapping, and OpenAI/LLM model names in one spot for live changes during the interview. | `OPENAI_MODEL_CHAT = "gpt-4o-mini"`, `TTS_VOICES` |
| `backend/product_recommendation.py` | **Deterministic Recommendation Engine:** Parses budget (e.g. 70k, 1 lakh) and intent (coding, student, gaming) from natural language; scores and filters catalog records from `products.csv`. Never allows LLM hallucination. | `recommend_products(...)`, `parse_budget_from_text(...)` |
| `backend/rag.py` | **TF-IDF & NumPy RAG Engine:** Ingests all 8 knowledge base text files, chunks paragraphs, and performs cosine similarity vector search using NumPy. Runs 100% offline with zero external model downloads. | `ElectroMartRAG.retrieve(...)`, `get_context(...)` |
| `backend/lead_qualification.py` | **BANT Lead Scoring:** Extracts requirement, budget, timeline, contact, and intent using regex. Calculates 0–100 score based on 5 weighted criteria and classifies into HOT, WARM, or COLD. | `LEAD_SCORING_WEIGHTS`, `extract_lead_from_conversation(...)` |
| `backend/sentiment.py` | **Word-Boundary Sentiment Engine:** Evaluates customer sentiment (-1.0 to 1.0). Uses regex word boundaries (`\b`) to eliminate false-negative triggers from sub-words. Detects human supervisor escalation flags. | `analyze_sentiment(...)`, `should_escalate(...)` |
| `backend/appointment.py` | **Dual-Engine Appointment System:** Dedicated manual booking portal (CRUD with edit and cancel) plus 5-step conversational voice booking flow. Validates operating hours (10 AM to 8:30 PM), prevents past dates and duplicate bookings, and formats RFC 5545 `.ics` invites. | `book_appointment_in_db(...)`, `update_appointment_in_db(...)`, `validate_appointment_slot(...)` |
| `backend/speech_to_text.py` | **Speech-to-Text Module:** Interacts with OpenAI Whisper API or Free SpeechRecognition to transcribe inbound audio and detect spoken language (English/Telugu/Kannada/Hindi). | `transcribe_audio_ai(...)`, `transcribe_audio_free(...)` |
| `backend/text_to_speech.py` | **Text-to-Speech Module:** Generates spoken audio using Microsoft Edge Neural voices (`en-IN-NeerjaNeural`, `te-IN-ShrutiNeural`, `kn-IN-SapnaNeural`, `hi-IN-SwaraNeural`). Generates unique file paths to eliminate Windows file-locking conflicts. | `text_to_speech(...)`, `_synthesize_async(...)` |
| `backend/summarizer.py` | **Call Summarizer:** Aggregates customer requirements, category, budget, objections, lead score, and generates structured executive summary records in SQLite. | `generate_call_summary(...)` |
| `backend/ai_agent.py` | **Agent Orchestrator:** Connects RAG, product recommendation, OpenAI LLM (or rule-based Demo Mode), lead qualification, and database persistence into an end-to-end sales turn. | `execute_sales_turn(...)`, `DEMO_REPLIES` |
| `database/models.py` | **SQLAlchemy ORM Models:** Defines relational schema for `Customer`, `Lead`, `Call`, `Message`, `Appointment`, `RecommendedProduct`, and `CallSummary`. | `class Lead(Base)`, `class Appointment(Base)` |
| `database/db.py` | **Database Session & Auto-Seeder:** Connects to SQLite (`electromart.db`). Checks on startup if tables are empty and automatically populates synthetic records from `data/*.csv`. | `init_db()`, `seed_initial_data()` |

---

## 🎯 20 Technical Interview Questions & Expert Answers

### 1. Why did you choose a dual-mode (Demo Mode vs. OpenAI API) architecture?
**Answer:** In production and technical hiring challenges, external API keys can expire, hit rate limits, or run out of quota. By designing a deterministic Demo Mode that leverages TF-IDF and regex scoring, the application is 100% demo-ready out of the box with zero paid API keys, while dynamically activating OpenAI (GPT-4o-mini / Whisper) when `OPENAI_API_KEY` is provided.

### 2. How did you prevent the LLM from hallucinating product specifications and prices?
**Answer:** I separated factual product retrieval from conversational generation. The recommendation engine (`backend/product_recommendation.py`) acts as the single source of truth, filtering and scoring verified rows directly from `products.csv`. The retrieved products and their exact prices are injected into the LLM system prompt as immutable constraints.

### 3. How does your RAG pipeline work without heavy embedding model downloads?
**Answer:** We implemented a TF-IDF vectorizer with bi-grams coupled with NumPy cosine similarity in `backend/rag.py`. It chunks all 8 knowledge base documents at application startup, builds a sparse vector space, and computes cosine similarity in sub-5 milliseconds without downloading gigabytes of model weights.

### 4. What was the false-negative sentiment bug and how did you resolve it?
**Answer:** Earlier sentiment implementations checked substrings (`any(kw in word)`). Because the negative keyword list contained `"no"`, polite customer queries mentioning `"electronics"`, `"innovative"`, or `"know"` triggered false negative sentiment and erroneously displayed the supervisor escalation alert. I resolved this by applying regex word boundaries (`\bkw\b`) and checking for stand-alone words only.

### 5. Why did you use Pydantic for lead qualification?
**Answer:** Pydantic provides runtime type validation, constraints (e.g. `score: int = Field(ge=0, le=100)`), and seamless serialization to dictionaries and JSON for database storage and REST API responses.

### 6. How is lead scoring calculated?
**Answer:** We use an objective BANT matrix stored in `LEAD_SCORING_WEIGHTS`:
- Clear product requirement: 20 pts
- Budget specified: 20 pts
- Purchase timeline within 30 days: 25 pts
- Contact information: 15 pts
- Strong purchase intent: 20 pts
Leads scoring 70–100 are HOT, 40–69 WARM, and 0–39 COLD.

### 7. How does the system handle multi-turn conversation memory?
**Answer:** In `backend/ai_agent.py`, conversation history is passed into `execute_sales_turn(...)`. We maintain the last 10 turns (`MAX_HISTORY_TURNS = 10`) while tracking extracted entities (budget, category, purpose, customer name, phone, email, and multi-step booking state) across turns so the assistant never repeatedly asks for already provided details.

### 8. How did you prevent database conflicts and duplicate appointment bookings?
**Answer:** In `backend/appointment.py`, before committing an appointment, the system executes an atomic query checking for existing active bookings with matching customer phone/email, date, and time slot. It also verifies operating hours (10:00 AM – 08:30 PM) and rejects past dates. If a slot is taken, it dynamically queries `get_available_slots(...)` and suggests available alternative times.

### 9. How do you generate calendar files?
**Answer:** In `generate_ics_content(...)`, we construct an RFC 5545-compliant text string containing VCALENDAR and VEVENT blocks with UTC timestamps and unique UUIDs. Streamlit provides an instant download button for the generated `.ics` file.

### 10. How do you support multilingual interaction (English, Telugu, Kannada, and Hindi)?
**Answer:** OpenAI Whisper and SpeechRecognition identify native Unicode script ranges (`\u0C00-\u0C7F` for Telugu, `\u0C80-\u0CFF` for Kannada, `\u0900-\u097F` for Hindi, and Latin for English) and transliterated keywords. The AI agent prompt instructs the model to respond in the user's language, and `backend/text_to_speech.py` routes text to Microsoft Edge Neural voices (`te-IN-ShrutiNeural`, `kn-IN-SapnaNeural`, `hi-IN-SwaraNeural`, and `en-IN-NeerjaNeural`). State is preserved even when customers switch languages mid-conversation.

### 11. How do you prevent Windows file-locking errors with Edge-TTS?
**Answer:** In Windows, if an audio file is being played by the browser, writing to the same static path causes `[WinError 32] PermissionError`. We generate unique file paths per turn using `uuid.uuid4().hex[:8]`.

### 12. How does the system auto-seed demo data?
**Answer:** On startup, `database/db.py` checks if the customer table has fewer than 5 records. If empty, it parses `data/products.csv`, `data/customers.csv`, `data/sample_leads.csv`, and `data/appointments.csv`, seeding relational rows into SQLite.

### 13. How did you handle audio re-read issues in Streamlit?
**Answer:** On Streamlit reruns, `st.audio_input` file pointers can reach EOF and return empty bytes (`b""`), causing transcription errors. We calculate an audio byte hash and cache it in `st.session_state` so each recording is only processed once.

### 14. How would you scale this application to 100,000 concurrent users?
**Answer:**
1. Migrate from SQLite to PostgreSQL with read replicas and connection pooling (PgBouncer).
2. Replace HTTP audio uploads with WebRTC bidirectional audio streaming (LiveKit / Twilio).
3. Move in-memory TF-IDF to a distributed vector database like Qdrant or Pinecone.
4. Deploy containerized FastAPI pods on Kubernetes with horizontal pod autoscaling.

### 15. What are the advantages of FastAPI over Flask or Django for this use case?
**Answer:** FastAPI provides native asynchronous request handling, automatic OpenAPI/Swagger documentation, strict Pydantic request/response validation, and high throughput performance comparable to NodeJS and Go.

### 16. What is the role of `data/data_dictionary.md`?
**Answer:** It documents every column name, data type, description, and sample value across all 7 synthetic datasets, ensuring maintainability and compliance with enterprise data governance standards.

### 17. How does the agent handle budget constraints when recommending products?
**Answer:** `backend/product_recommendation.py` extracts the budget integer and filters catalog products. It scores in-budget products higher and applies penalty weights to over-budget items while presenting suitable alternatives.

### 18. Why is SQLite sufficient for an MVP and when should it be replaced?
**Answer:** SQLite requires zero configuration, is serverless, embeds directly within the file system, and supports ACID transactions. It should be replaced with PostgreSQL when concurrent write volume exceeds hundreds of transactions per second.

### 19. How do you ensure the privacy of customer data in this repository?
**Answer:** All customer records use RFC 2606 reserved example domains (`@example.com`) and synthetic phone numbers. No real personal data or external production credentials exist in the codebase.

### 20. How can you demonstrate live changes during an interview?
**Answer:** All live variables are consolidated in single dictionaries:
- Change scoring weights in `backend/lead_qualification.py` (`LEAD_SCORING_WEIGHTS`).
- Change model or voices in `backend/config.py` (`OPENAI_MODEL_CHAT`, `TTS_VOICES`).
- Change agent personality in `backend/ai_agent.py` (`ELECTROMART_SYSTEM_PROMPT`).
