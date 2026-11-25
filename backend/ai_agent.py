"""
ElectroMart India — AI Sales Voice Agent Orchestrator
Coordinates RAG context retrieval, catalog product recommendations, Gemini LLM reasoning
(with rule-based Demo Mode fallback), BANT lead scoring, sentiment tracking, and booking.
"""
import os
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

from backend.config import (
    COMPANY_NAME, AGENT_NAME, GEMINI_MODEL_CHAT,
    MAX_HISTORY_TURNS, AGENT_ROLE_DESCRIPTION
)
from backend.rag import rag_engine
from backend.product_recommendation import recommend_products, format_recommendations_for_agent
from backend.lead_qualification import extract_lead_from_conversation, ExtractedLead
from backend.sentiment import analyze_sentiment, should_escalate
from backend.appointment import parse_natural_datetime, book_appointment_in_db, generate_ics_content
from database.db import SessionLocal, init_db
from database.models import Customer, Lead, Call, Message, RecommendedProduct

load_dotenv()

# System Prompt
ELECTROMART_SYSTEM_PROMPT = f"""
{AGENT_ROLE_DESCRIPTION}

GUIDELINES FOR CONVERSATION:
1. Greet the customer warmly and politely in English or Hindi (match customer language).
2. Understand what they are looking for (laptops, smartphones, tablets, or accessories).
3. Ask about their budget and intended use (e.g. programming, gaming, students, office, photography).
4. Recommend products ONLY from the provided CATALOG RECOMMENDATIONS context. Do not invent products or prices.
5. Explain clearly why each recommended product suits their needs.
6. Answer questions about pricing, warranty, and return policies using the KNOWLEDGE BASE context.
7. Offer to arrange a store visit or consultation demo.
8. Keep answers concise, consultative, and professional (under 3-4 sentences per turn).
"""

# Realistic Demo Mode response bank for offline testing
DEMO_REPLIES = {
    "greeting": f"Hello! Welcome to {COMPANY_NAME}. I'm {AGENT_NAME}, your AI electronics sales advisor. Are you looking for laptops, smartphones, tablets, or accessories today?",
    "programming_laptop": (
        "Based on your requirements for programming and multitasking, I recommend three great options:\n"
        "1. **CodeMaster Pro 15** (₹64,999) — 13th Gen Intel Core i5, 16GB DDR5 RAM, and a crisp 2K display.\n"
        "2. **ZenithBook Air 15** (₹48,999) — AMD Ryzen 5, 16GB RAM, budget-friendly for daily coding.\n"
        "3. **DevForge Extreme 16** (₹79,999) — AMD Ryzen 7 with dedicated RTX 3050 GPU for heavy Docker & ML."
    ),
    "which_is_best": (
        "Based on your budget and programming requirements, I highly recommend the **CodeMaster Pro 15** (₹64,999). "
        "Its high-performance Intel 13th Gen H-series processor and 16GB DDR5 memory handle multiple IDEs, "
        "browser tabs, and local servers effortlessly without lag."
    ),
    "student_laptop": (
        "For students, our top choice is the **VoltBook Student 14** at ₹34,999! "
        "It features an Intel Core i3 12th Gen processor, 8GB RAM, and 8 hours of battery life. "
        "Plus, our Student Tech Pass offer gives you an additional ₹2,500 instant discount with your college ID."
    ),
    "gaming_laptop": (
        "For gaming under ₹1,00,000, the **CyberPulse G15** (₹94,999) is our powerhouse performer! "
        "It features an AMD Ryzen 7 7840HS, 16GB DDR5, and NVIDIA RTX 4060 8GB GPU with a fluid 165Hz QHD panel."
    ),
    "camera_phone": (
        "For photography and short video reels, I recommend the **Zenith CamPro 5G** (₹34,999). "
        "It comes equipped with triple 50MP Sony sensors with Optical Image Stabilization (OIS) and 67W fast charging."
    ),
    "store_visit": (
        "Certainly! We'd be delighted to host you for a hands-on demo at our showroom. "
        "What date and time would be convenient for your visit?"
    ),
    "warranty_policy": (
        "All our electronics include official brand warranty (1 to 3 years depending on the model). "
        "We also offer a 7-day hassle-free doorstep replacement guarantee for any transit or manufacturing defect."
    ),
    "offers": (
        "We have great offers running right now! Including 0% No-Cost EMI for up to 12 months, "
        "up to ₹5,000 extra exchange bonus on trading old devices, and ₹2,500 off on laptops with a valid student ID."
    ),
    "hindi_laptop": (
        "नमस्ते! कोडिंग और ऑफिस के काम के लिए ZenithBook Air 15 (₹48,999) और CodeMaster Pro 15 (₹64,999) "
        "सबसे बेहतरीन विकल्प हैं। इनमें 16GB RAM और तेज़ प्रोसेसर मिलता है। क्या आप हमारे शोरूम में लाइव डेमो देखना चाहेंगे?"
    )
}


def get_gemini_client():
    """Return google-genai client if GEMINI_API_KEY is present in environment, else None."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Gemini client init notice: {e}")
        return None


def is_demo_mode() -> bool:
    """True when no Gemini API key is configured."""
    return get_gemini_client() is None


def _generate_demo_reply(user_input: str, recs: List[Dict], context: str) -> str:
    """Generate realistic rule-based reply matching ElectroMart scenarios."""
    t = user_input.lower()

    if any(w in t for w in ["नमस्ते", "हिंदी", "लैपटॉप", "दाम", "कीमत", "वारंटी"]):
        return DEMO_REPLIES["hindi_laptop"]

    if any(w in t for w in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return DEMO_REPLIES["greeting"]

    if "which one is best" in t or "which is best" in t or "which should i buy" in t:
        return DEMO_REPLIES["which_is_best"]

    if any(w in t for w in ["program", "code", "coding", "developer", "70,000", "70000", "70k"]):
        return DEMO_REPLIES["programming_laptop"]

    if any(w in t for w in ["student", "college", "school", "35k", "35,000"]):
        return DEMO_REPLIES["student_laptop"]

    if any(w in t for w in ["gaming", "game", "rtx", "cyberpulse", "1 lakh", "100000"]):
        return DEMO_REPLIES["gaming_laptop"]

    if any(w in t for w in ["camera", "photo", "vlog", "reel", "campro"]):
        return DEMO_REPLIES["camera_phone"]

    if any(w in t for w in ["visit", "store", "showroom", "tomorrow", "come"]):
        return DEMO_REPLIES["store_visit"]

    if any(w in t for w in ["warranty", "return", "replace", "guarantee"]):
        return DEMO_REPLIES["warranty_policy"]

    if any(w in t for w in ["offer", "discount", "emi", "cashback", "exchange"]):
        return DEMO_REPLIES["offers"]

    # If recommendation engine found products, present them
    if recs:
        return f"Based on your requirements, here are our top catalog recommendations:\n\n{format_recommendations_for_agent(recs)}\n\nWould you like to book a store demo to test these hands-on?"

    # Context fallback
    if context and len(context) > 40:
        return f"According to our ElectroMart catalog: {context[:280]}... Would you like more details on this model?"

    return f"I can certainly help you with that! Are you looking for a laptop, smartphone, tablet, or accessories, and what budget do you have in mind?"


def execute_sales_turn(
    call_id: str,
    user_input: str,
    language: str = "en",
    history: Optional[List[Dict]] = None
) -> Dict:
    """
    Execute one full conversational sales turn.
    Returns:
      {reply, mode, language, sentiment, lead, sources, recommendations, booking, ics_content}
    """
    db = SessionLocal()
    history = history or []

    try:
        start_t = time.time()

        # 1. RAG Context Retrieval
        rag_sources = rag_engine.retrieve(user_input, top_k=3)
        rag_context = rag_engine.get_context(user_input, top_k=3)

        # 2. Product Recommendations
        recs = recommend_products(user_input, max_results=3)

        # 3. Sentiment Analysis
        sentiment_label, sentiment_score = analyze_sentiment(user_input)

        # 4. Lead Extraction & BANT Scoring
        all_text = " ".join([h.get("content", "") for h in history]) + " " + user_input
        extracted_lead: ExtractedLead = extract_lead_from_conversation(all_text)

        # 5. Generate Response (Gemini or Demo Mode)
        client = get_gemini_client()
        agent_reply = ""
        mode = "Demo Mode"

        if client:
            try:
                from google.genai import types
                prompt_messages = f"""
{ELECTROMART_SYSTEM_PROMPT}

KNOWLEDGE BASE CONTEXT:
{rag_context}

CATALOG RECOMMENDATIONS:
{format_recommendations_for_agent(recs)}

CONVERSATION HISTORY:
"""
                for h in history[-MAX_HISTORY_TURNS:]:
                    prompt_messages += f"{h.get('role', 'user').upper()}: {h.get('content', '')}\n"

                prompt_messages += f"USER: {user_input}\nAGENT:"

                res = client.models.generate_content(
                    model=GEMINI_MODEL_CHAT,
                    contents=prompt_messages
                )
                agent_reply = res.text.strip()
                mode = "Gemini 2.5 Flash"
            except Exception as e:
                print(f"Gemini API error, using demo fallback: {e}")
                agent_reply = _generate_demo_reply(user_input, recs, rag_context)
                mode = f"Demo Mode (API error: {str(e)[:40]})"
        else:
            agent_reply = _generate_demo_reply(user_input, recs, rag_context)
            mode = "Demo Mode"

        # 6. Appointment Booking Detection
        booking_result = None
        ics_data = None
        lower_input = user_input.lower()
        if any(w in lower_input for w in ["book", "confirm", "visit", "pm", "am", "tomorrow", "appointment", "slot"]):
            # If user mentions time or says yes/tomorrow
            if any(w in lower_input for w in ["4pm", "pm", "am", "tomorrow", "today", "slot", "4:00"]):
                target_date, target_time_str = parse_natural_datetime(user_input)
                cust_email = extracted_lead.email or "customer@example.com"
                cust_name = extracted_lead.name or "Valued Customer"

                success, b_msg, appt = book_appointment_in_db(
                    db=db,
                    customer_name=cust_name,
                    customer_email=cust_email,
                    customer_phone=extracted_lead.phone,
                    date_val=target_date,
                    time_str=target_time_str,
                    appointment_type="Store Visit",
                    interested_product=recs[0]["product_name"] if recs else "Electronics Demo",
                    city=extracted_lead.city or "Mumbai",
                    notes="Booked via AI Voice Agent"
                )
                if success:
                    booking_result = {
                        "status": "success",
                        "message": b_msg,
                        "date": target_date.strftime("%Y-%m-%d"),
                        "time": target_time_str
                    }
                    ics_data = generate_ics_content(
                        cust_name, target_date, target_time_str,
                        product=recs[0]["product_name"] if recs else "Electronics"
                    )
                    agent_reply += f" [System: Store demo confirmed for {target_date.strftime('%d %B')} at {target_time_str}. Calendar invite ready.]"

        # 7. Persist to Database
        # Upsert Lead
        lead = db.query(Lead).filter(Lead.call_id == call_id).first()
        if not lead:
            lead = Lead(
                call_id=call_id,
                name=extracted_lead.name,
                email=extracted_lead.email,
                phone=extracted_lead.phone,
                city=extracted_lead.city,
                interested_category=extracted_lead.interested_category,
                budget=extracted_lead.budget,
                requirement=extracted_lead.requirement,
                purchase_timeline=extracted_lead.purchase_timeline,
                purchase_intent=extracted_lead.purchase_intent,
                score=extracted_lead.score,
                qualification_status=extracted_lead.status
            )
            db.add(lead)
        else:
            if extracted_lead.name: lead.name = extracted_lead.name
            if extracted_lead.email: lead.email = extracted_lead.email
            if extracted_lead.phone: lead.phone = extracted_lead.phone
            if extracted_lead.city: lead.city = extracted_lead.city
            if extracted_lead.interested_category: lead.interested_category = extracted_lead.interested_category
            if extracted_lead.budget: lead.budget = extracted_lead.budget
            if extracted_lead.requirement: lead.requirement = extracted_lead.requirement
            if extracted_lead.purchase_timeline: lead.purchase_timeline = extracted_lead.purchase_timeline
            lead.score = max(lead.score, extracted_lead.score)
            lead.qualification_status = extracted_lead.status

        # Save Messages
        db.add(Message(call_id=call_id, sender="user", text=user_input, sentiment_label=sentiment_label, sentiment_score=sentiment_score))
        db.add(Message(call_id=call_id, sender="agent", text=agent_reply, sentiment_label="positive", sentiment_score=0.5))

        # Save Recommended Products
        for r in recs:
            db.add(RecommendedProduct(
                call_id=call_id,
                product_id=r["product_id"],
                product_name=r["product_name"],
                price_inr=r["price_inr"],
                reason=r["reason"]
            ))

        db.commit()

        latency_ms = int((time.time() - start_t) * 1000)

        return {
            "reply": agent_reply,
            "mode": mode,
            "language": language,
            "sentiment": {"label": sentiment_label, "score": sentiment_score},
            "lead": extracted_lead.dict(),
            "sources": [{"text": chunk[:140], "score": score} for chunk, score in rag_sources],
            "recommendations": recs,
            "booking": booking_result,
            "ics_content": ics_data,
            "latency_ms": latency_ms
        }
    finally:
        db.close()
