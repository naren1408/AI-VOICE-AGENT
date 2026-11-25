# ElectroMart India — Autonomous AI Sales Voice Agent
**Technical Placement Challenge Executive Report**

---

## 1. Executive Summary & Problem Statement
In the multi-brand electronics retail sector, brick-and-mortar and omnichannel retailers face significant revenue loss from three key operational friction points:
1. **Prolonged Inquiry Response Times:** Customers seeking product specifications (e.g. processor benchmarks, RAM expandability, warranty conditions) drop off when sales staff are unavailable.
2. **Inconsistent Consultation Quality:** Floor staff often push high-margin inventory rather than matching products to customers' precise technical needs and budget constraints.
3. **Omnichannel Booking Gaps:** Lack of seamless bridge between online digital inquiries and physical showroom demo appointments.

**ElectroMart India** solves these challenges with an autonomous AI sales voice advisor (`Anya`) that engages prospects in natural English, Telugu, and Kannada, grounds consultations strictly in verified product catalog specifications, provides deterministic budget-adherent recommendations, qualifies leads via BANT criteria, and schedules conflict-free showroom visits.

---

## 2. Technical Architecture & Component Design
The system utilizes a clean, decoupled full-stack architecture:
- **Presentation Layer:** Streamlit enterprise dashboard (`app.py`) built with a light, clean SaaS aesthetic featuring 3 operational tabs: Live Sales Call, Products & CRM Pipeline, and Sales BI Insights.
- **REST API Gateway:** FastAPI service (`backend/main.py`) exposing standardized endpoints (`/call/start`, `/call/{id}/text`, `/call/{id}/audio`, `/call/{id}/end`, `/products`, `/leads`, `/appointments`, `/insights`).
- **Intelligence & RAG Engine:** Multi-document TF-IDF vectorizer coupled with NumPy cosine similarity (`backend/rag.py`), ingesting 8 domain documents (company profile, catalog, pricing, policies, recommendation guides, FAQs, and comparisons). Optionally leverages Gemini 2.5 Flash via `google-genai` SDK.
- **Deterministic Recommendation Engine:** Source-of-truth matching logic (`backend/product_recommendation.py`) that strictly filters and scores catalog products without hallucination.
- **Persistence Layer:** SQLite with SQLAlchemy ORM (`database/db.py`), auto-seeded with 25 products, 20 customers, 15 leads, and 10 appointments.

---

## 3. Core Capabilities & Innovations
1. **Zero-API-Key Demo Mode:** Runs completely offline with pre-seeded datasets, smart keyword-to-RAG routing, and deterministic scoring.
2. **BANT Lead Scoring Matrix:**
   - Clear product requirement: 20 pts
   - Budget specified: 20 pts
   - Purchase timeline within 30 days: 25 pts
   - Contact information (email/phone): 15 pts
   - Strong purchase intent: 20 pts
   - Priority Bands: **HOT** (70–100), **WARM** (40–69), **COLD** (0–39).
3. **Word-Boundary Sentiment Analysis:** Evaluates customer sentiment (-1.0 to 1.0) using regex word boundaries (`\b`), preventing false negative escalations from substrings.
4. **Conflict-Free Appointment Scheduling:** Real-time business hours validation (10:00 AM – 08:30 PM) and database locks preventing duplicate customer bookings, complete with RFC 5545 `.ics` file generation.

---

## 4. Production Scalability Strategy (100,000+ Concurrent Customers)
To transition this MVP to an enterprise retail deployment serving 100k+ concurrent users:
- **Audio Streaming:** Upgrade from HTTP multipart audio uploads to WebRTC bidirectional audio streaming (via LiveKit / Twilio Media Streams) to achieve sub-400ms voice turn latency.
- **State & Data Store:** Replace SQLite with managed PostgreSQL with read replicas; cache RAG embeddings, catalog queries, and customer sessions in Redis clusters.
- **Distributed Vector Search:** Migrate in-memory TF-IDF to Qdrant or Pinecone backed by dedicated embedding microservices.
- **Container Orchestration:** Deploy FastAPI workers on Kubernetes with Horizontal Pod Autoscaling (HPA) governed by active WebSocket connection depth.

---

## 5. Security & Compliance
- **Zero Exposed Secrets:** Central configuration via `.env` with strict `.gitignore` rules.
- **Fictional Data Isolation:** All synthetic customer emails use the RFC 2606 reserved `example.com` domain.
- **Catalog Grounding:** The LLM is strictly constrained from inventing non-existent models or unauthorized discounts.
