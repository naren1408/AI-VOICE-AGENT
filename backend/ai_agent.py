import os
import json
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from backend.rag import rag_pipeline
from backend.lead_qualification import (
    LeadQualificationData, calculate_lead_score, get_qualification_status, extract_lead_rule_based
)
from backend.sentiment import analyze_sentiment
from backend.appointment import (
    parse_natural_datetime, check_availability, book_appointment, generate_ics_content
)
from database.db import SessionLocal, init_db
from database.models import Lead, Call, Message, Appointment

load_dotenv()
init_db()  # Automatically ensure SQLite tables exist

# ==============================================================================
# CONFIGURATION VARIABLES (Keep in one identifiable place for easy live changes)
# ==============================================================================
GEMINI_MODEL_CHAT = "gemini-2.5-flash"
GEMINI_MODEL_AUDIO = "gemini-2.5-flash"
GEMINI_MODEL_EMBED = "text-embedding-004"

# ==============================================================================
# SYSTEM PROMPT (Clearly marked section for live-coding interview explanation)
# ==============================================================================
SALES_SYSTEM_PROMPT = """
You are Ava, a senior FinOps solutions advisor at CloudScale AI.
Your mission is to understand inbound prospect needs, answer questions strictly from the retrieved company knowledge base, qualify the lead, and book a technical demo.

COMMUNICATION GUIDELINES:
1. Be warm, professional, concise, and consultative (keep voice responses under 3 sentences).
2. Ground your answers strictly in the provided KNOWLEDGE BASE. If information is not in the knowledge base, politely say a solutions specialist will follow up. Never invent pricing or features.
3. Proactively guide the lead through the qualification flow:
   - Ask about their current cloud infrastructure size and pain points.
   - Clarify their purchase timeline and budget.
   - Collect their contact details (name and email).
   - Offer a tailored 30-minute demo slot (available Monday to Friday, 9 AM - 6 PM).
4. Language rule: Always reply in the exact same language used by the prospect (English or Hindi).
"""

# ==============================================================================
# PREDEFINED DEMO-MODE REPLIES (English & Hindi for guaranteed zero-key demo)
# ==============================================================================
DEMO_RESPONSES = {
    "pricing": (
        "CloudScale AI offers three pricing tiers: Starter at $499/month for up to 50 nodes, "
        "Professional at $1,499/month for up to 250 nodes with multi-cloud support, and custom Enterprise starting at $4,500/month. "
        "What size is your current cloud infrastructure?"
    ),
    "features": (
        "We specialize in automated compute rightsizing, Kubernetes pod autoscaling, and real-time FinOps cost governance, "
        "typically cutting AWS, GCP, and Azure waste by up to 45%. Are you looking to reduce multi-cloud spend?"
    ),
    "qualification_step": (
        "Thanks for sharing! We can certainly help you optimize that compute workload. "
        "To tailor the recommendations, what is your budget and expected timeline to implement a solution?"
    ),
    "contact_step": (
        "That fits right into our Professional tier. May I have your name and email address so I can set up a personalized environment?"
    ),
    "book_step": (
        "I'd love to schedule a 30-minute technical demonstration with our solutions engineer. "
        "Would tomorrow at 4:00 PM work well for you?"
    ),
    "hindi_response": (
        "नमस्ते! CloudScale AI आपके क्लाउड खर्च को 45% तक कम करने में मदद करता है। "
        "हमारा स्टार्टर प्लान $499 प्रति माह से शुरू होता है। क्या आप 30 मिनट का डेमो देखना चाहेंगे?"
    ),
    "fallback": (
        "I understand. CloudScale AI helps engineering teams automate cloud cost governance. "
        "Would you like to book a quick 30-minute demo to see live savings on your infrastructure?"
    )
}


def get_gemini_client():
    """Initialize modern Google GenAI Client if valid key exists, else None."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def is_demo_mode() -> bool:
    """Return True if running in zero-API-key Demo Mode."""
    return get_gemini_client() is None


def generate_demo_reply(user_text: str, language: str = "en") -> str:
    """Generate realistic sales responses for demo mode without LLM calls."""
    text_lower = user_text.lower()

    if language == "hi" or any(w in text_lower for w in ["namaste", "daam", "keemat", "kya", "bataiye"]):
        return DEMO_RESPONSES["hindi_response"]

    if any(w in text_lower for w in ["price", "cost", "pricing", "tier", "how much", "rate"]):
        return DEMO_RESPONSES["pricing"]
    elif any(w in text_lower for w in ["demo", "book", "slot", "tomorrow", "schedule", "meeting", "time"]):
        return "I can book that demo for you right away! What email address should I send the invite and calendar link to?"
    elif any(w in text_lower for w in ["budget", "timeline", "month", "quarter", "urgent", "$"]):
        return DEMO_RESPONSES["contact_step"]
    elif any(w in text_lower for w in ["node", "server", "aws", "kubernetes", "cloud", "waste", "optimize"]):
        return DEMO_RESPONSES["qualification_step"]
    elif "@" in text_lower:
        return "Thank you! I have your contact details. Would tomorrow at 4:00 PM work for your technical demo?"
    else:
        return DEMO_RESPONSES["fallback"]


def execute_sales_turn(
    call_id: str,
    user_input: str,
    language: str = "en",
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Execute complete conversational turn: STT/text -> RAG -> LLM/Demo -> Lead Score -> Sentiment -> DB."""
    start_time = time.time()
    db = SessionLocal()

    try:
        # 1. Retrieve knowledge base context
        client = get_gemini_client()
        retrieved_items = rag_pipeline.retrieve(user_input, top_k=3, client=client, embed_model=GEMINI_MODEL_EMBED)
        sources_text = "\n\n".join([chunk for chunk, score in retrieved_items])

        # 2. Generate agent response (Gemini Mode or Demo Mode)
        llm_start = time.time()
        agent_reply = ""
        mode = "Gemini Mode" if client else "Demo Mode"

        if client:
            try:
                # Format conversation memory (last 10 turns)
                conv_history_prompt = ""
                if history:
                    for turn in history[-10:]:
                        role = "Customer" if turn.get("role") == "user" else "Ava (CloudScale AI)"
                        conv_history_prompt += f"{role}: {turn.get('content', '')}\n"

                prompt = (
                    f"{SALES_SYSTEM_PROMPT}\n\n"
                    f"KNOWLEDGE BASE CONTEXT:\n{sources_text}\n\n"
                    f"CONVERSATION HISTORY:\n{conv_history_prompt}\n\n"
                    f"Customer ({language}): {user_input}\n"
                    f"Ava (respond concisely in {language}):"
                )

                res = client.models.generate_content(
                    model=GEMINI_MODEL_CHAT,
                    contents=prompt
                )
                agent_reply = res.text.strip()
            except Exception as err:
                mode = "Demo Mode (API Fallback)"
                agent_reply = generate_demo_reply(user_input, language)
        else:
            agent_reply = generate_demo_reply(user_input, language)

        llm_latency_ms = int((time.time() - llm_start) * 1000)

        # 3. Analyze turn sentiment
        sentiment_label, sentiment_score = analyze_sentiment(user_input)

        # 4. Check if user is booking an appointment in this turn
        text_for_booking = f"{user_input} {agent_reply}"
        booking_result = None
        ics_data = None

        if any(w in user_input.lower() for w in ["book", "confirm", "yes", "tomorrow", "pm", "am", "schedule", "slot"]):
            # Extract email if present
            lead_data = extract_lead_rule_based(user_input)
            if lead_data.email or any(w in user_input.lower() for w in ["tomorrow", "4pm", "slot", "yes"]):
                target_dt = parse_natural_datetime(user_input)
                # Check if we have an email from current input or DB lead
                existing_lead = db.query(Lead).filter(Lead.call_id == call_id).first()
                cust_email = lead_data.email or (existing_lead.email if existing_lead else "")
                cust_name = lead_data.name or (existing_lead.name if existing_lead else "Valued Client")

                if cust_email:
                    success, b_msg, appt = book_appointment(db, cust_name, cust_email, target_dt, call_id)
                    if success:
                        booking_result = {"status": "success", "message": b_msg, "slot": target_dt.isoformat()}
                        ics_data = generate_ics_content(cust_name, target_dt)
                        agent_reply += f" [System: Confirmed demo for {target_dt.strftime('%b %d at %I:%M %p')}. Confirmation invite created.]"

        # 5. Extract & Upsert Lead qualification
        combined_text = user_input + " " + " ".join([h.get("content", "") for h in (history or [])])
        extracted_lead = extract_lead_rule_based(combined_text)
        lead_score = calculate_lead_score(extracted_lead)
        lead_status = get_qualification_status(lead_score)

        lead = db.query(Lead).filter(Lead.call_id == call_id).first()
        if not lead:
            lead = Lead(
                call_id=call_id,
                name=extracted_lead.name,
                email=extracted_lead.email,
                phone=extracted_lead.phone,
                company=extracted_lead.company,
                need=extracted_lead.need,
                budget=extracted_lead.budget,
                timeline=extracted_lead.timeline,
                is_decision_maker=extracted_lead.is_decision_maker,
                score=lead_score,
                qualification_status=lead_status
            )
            db.add(lead)
        else:
            # Update fields without overwriting non-empty values with empties
            if extracted_lead.name: lead.name = extracted_lead.name
            if extracted_lead.email: lead.email = extracted_lead.email
            if extracted_lead.phone: lead.phone = extracted_lead.phone
            if extracted_lead.company: lead.company = extracted_lead.company
            if extracted_lead.need: lead.need = extracted_lead.need
            if extracted_lead.budget: lead.budget = extracted_lead.budget
            if extracted_lead.timeline: lead.timeline = extracted_lead.timeline
            if extracted_lead.is_decision_maker: lead.is_decision_maker = True
            lead.score = max(lead.score, lead_score)
            lead.qualification_status = get_qualification_status(lead.score)

        # 6. Save messages to SQLite
        call_obj = db.query(Call).filter(Call.id == call_id).first()
        if not call_obj:
            call_obj = Call(id=call_id, language=language)
            db.add(call_obj)

        msg_user = Message(
            call_id=call_id,
            sender="user",
            text=user_input,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            llm_latency_ms=llm_latency_ms
        )
        msg_agent = Message(
            call_id=call_id,
            sender="agent",
            text=agent_reply,
            sentiment_label="positive",
            sentiment_score=0.5,
            llm_latency_ms=llm_latency_ms
        )
        db.add(msg_user)
        db.add(msg_agent)
        db.commit()

        return {
            "reply": agent_reply,
            "mode": mode,
            "language": language,
            "sentiment": {"label": sentiment_label, "score": sentiment_score},
            "lead": {
                "name": lead.name,
                "email": lead.email,
                "company": lead.company,
                "budget": lead.budget,
                "timeline": lead.timeline,
                "score": lead.score,
                "status": lead.qualification_status,
                "is_decision_maker": lead.is_decision_maker
            },
            "sources": [chunk for chunk, sim in retrieved_items],
            "booking": booking_result,
            "ics_content": ics_data,
            "latency": {
                "stt_ms": 0,
                "llm_ms": llm_latency_ms,
                "tts_ms": 0,
                "total_ms": int((time.time() - start_time) * 1000)
            }
        }
    finally:
        db.close()


def generate_call_summary(call_id: str) -> Dict[str, Any]:
    """Generate structured summary, key points, objections, and next steps for ended call."""
    db = SessionLocal()
    try:
        messages = db.query(Message).filter(Message.call_id == call_id).order_by(Message.timestamp).all()
        lead = db.query(Lead).filter(Lead.call_id == call_id).first()
        call_obj = db.query(Call).filter(Call.id == call_id).first()

        transcript = "\n".join([f"{m.sender.upper()}: {m.text}" for m in messages])

        # Rule-based fallback summary
        summary = f"Inbound sales interaction with {lead.name if lead and lead.name else 'prospect'}. Discussed CloudScale AI compute rightsizing and tier options."
        key_points = "Prospect reviewed CloudScale AI tiers, shared cloud infrastructure requirements, and explored automated FinOps cost reduction."
        objections = "Evaluated tier pricing and fit for current infrastructure scale."
        next_steps = "Solutions engineer to conduct 30-minute technical demonstration and architecture review."

        client = get_gemini_client()
        if client and transcript:
            try:
                summary_prompt = (
                    "Summarize this enterprise sales call in JSON with keys: "
                    "'summary' (2 sentences), 'key_points' (bullet points), 'objections', 'next_steps'.\n\n"
                    f"Transcript:\n{transcript}"
                )
                res = client.models.generate_content(
                    model=GEMINI_MODEL_CHAT,
                    contents=summary_prompt
                )
                # Try parsing JSON or fall back
                raw = res.text.strip()
                if raw.startswith("```json"):
                    raw = raw[7:-3].strip()
                parsed = json.loads(raw)
                summary = parsed.get("summary", summary)
                key_points = str(parsed.get("key_points", key_points))
                objections = str(parsed.get("objections", objections))
                next_steps = str(parsed.get("next_steps", next_steps))
            except Exception:
                pass

        if call_obj:
            call_obj.summary = summary
            call_obj.key_points = key_points
            call_obj.objections = objections
            call_obj.next_steps = next_steps
            call_obj.final_score = lead.score if lead else 0
            call_obj.final_sentiment = "positive"
            db.commit()

        return {
            "summary": summary,
            "key_points": key_points,
            "objections": objections,
            "next_steps": next_steps,
            "score": lead.score if lead else 0,
            "status": lead.qualification_status if lead else "COLD"
        }
    finally:
        db.close()
