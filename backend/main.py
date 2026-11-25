"""
ElectroMart India — FastAPI Application
REST API Gateway for Voice & Conversational Sales Interaction, Catalog, Leads, and CRM Integration.
Run with: python -m uvicorn backend.main:app --port 8000 --reload
"""
import os
import uuid
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db, init_db
from database.models import Customer, Lead, Call, Message, Appointment, CallSummary, RecommendedProduct
from backend.ai_agent import execute_sales_turn, is_demo_mode, get_gemini_client
from backend.product_recommendation import load_products_df, recommend_products
from backend.lead_qualification import extract_lead_from_conversation
from backend.speech_to_text import transcribe_audio_gemini
from backend.text_to_speech import text_to_speech
from backend.summarizer import generate_call_summary
from backend.config import COMPANY_NAME, AGENT_NAME

# Initialize FastAPI application
app = FastAPI(
    title="ElectroMart India — AI Sales Voice Agent API",
    version="1.0.0",
    description="Autonomous Electronics Retail Sales Voice Agent: Recommendations, Lead Scoring, Booking & CRM."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# --- Pydantic Request / Response Schemas ---
class CallStartResponse(BaseModel):
    call_id: str
    message: str
    mode: str


class TextTurnRequest(BaseModel):
    text: str
    language: Optional[str] = "en"
    history: Optional[List[Dict[str, Any]]] = []


class CallEndRequest(BaseModel):
    messages: Optional[List[Dict[str, Any]]] = []


class WebhookPayload(BaseModel):
    event: str
    data: Dict[str, Any]


# --- Endpoints ---
@app.get("/health")
def health_check():
    """Health check endpoint indicating service status and active AI mode."""
    return {
        "status": "healthy",
        "company": COMPANY_NAME,
        "agent": AGENT_NAME,
        "mode": "Demo Mode" if is_demo_mode() else "Gemini 2.5 Flash",
        "timestamp": time.time()
    }


@app.post("/call/start", response_model=CallStartResponse)
def start_call(db: Session = Depends(get_db)):
    """Initialize a new customer sales session with a unique call ID."""
    call_id = f"CALL-{str(uuid.uuid4())[:8].upper()}"
    new_call = Call(id=call_id)
    db.add(new_call)
    db.commit()

    mode_label = "Demo Mode" if is_demo_mode() else "Gemini 2.5 Flash"
    return CallStartResponse(
        call_id=call_id,
        message=f"Welcome to {COMPANY_NAME}! Session {call_id} initialized in {mode_label}.",
        mode=mode_label
    )


@app.post("/call/{call_id}/text")
def handle_text_turn(call_id: str, payload: TextTurnRequest):
    """Process a conversational text turn through RAG, Recommendation Engine, and Agent."""
    result = execute_sales_turn(
        call_id=call_id,
        user_input=payload.text,
        language=payload.language or "en",
        history=payload.history or []
    )
    return result


@app.post("/call/{call_id}/audio")
async def handle_audio_turn(call_id: str, audio: UploadFile = File(...)):
    """Transcribe inbound customer audio, process sales turn, and synthesize voice audio."""
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    temp_audio_in = os.path.join(temp_dir, f"{call_id}_in.wav")

    content = await audio.read()
    with open(temp_audio_in, "wb") as f:
        f.write(content)

    client = get_gemini_client()
    user_transcript, detected_lang = transcribe_audio_gemini(temp_audio_in, client)
    if not user_transcript or user_transcript.startswith("Audio transcription error"):
        user_transcript = "What are your top laptop recommendations?"

    # Execute sales turn
    result = execute_sales_turn(
        call_id=call_id,
        user_input=user_transcript,
        language=detected_lang
    )

    # Synthesize audio response
    audio_path = text_to_speech(result["reply"], language=detected_lang)
    result["audio_path"] = audio_path
    result["transcript"] = user_transcript

    return result


@app.post("/call/{call_id}/end")
def end_call(call_id: str, payload: CallEndRequest, db: Session = Depends(get_db)):
    """End a call session, generate executive summary, and save to CRM."""
    all_text = " ".join([m.get("text", "") for m in payload.messages])
    extracted_lead = extract_lead_from_conversation(all_text)
    recs = recommend_products(all_text, max_results=3)

    summary = generate_call_summary(
        db=db,
        call_id=call_id,
        extracted_lead=extracted_lead,
        recommended_prods=recs,
        messages=payload.messages
    )

    return {
        "status": "completed",
        "call_id": call_id,
        "summary": summary.requirements,
        "recommended_products": summary.recommended_products,
        "lead_score": summary.lead_score,
        "lead_status": summary.lead_status,
        "next_action": summary.next_action
    }


@app.get("/products")
def list_products(
    category: Optional[str] = Query(None, description="Filter by Laptops, Smartphones, Tablets, Accessories"),
    max_price: Optional[int] = Query(None, description="Maximum price in INR")
):
    """Retrieve electronics catalog products with optional filtering."""
    df = load_products_df()
    if df.empty:
        return []

    if category:
        df = df[df["category"].str.lower() == category.lower()]
    if max_price:
        df = df[df["price_inr"] <= max_price]

    return df.fillna("N/A").to_dict(orient="records")


@app.get("/leads")
def list_leads(
    status: Optional[str] = Query(None, description="Filter by HOT, WARM, COLD"),
    db: Session = Depends(get_db)
):
    """Retrieve all sales leads from CRM."""
    q = db.query(Lead)
    if status:
        q = q.filter(Lead.qualification_status == status.upper())
    leads = q.order_by(Lead.updated_at.desc()).all()
    return [
        {
            "id": l.id,
            "name": l.name,
            "email": l.email,
            "phone": l.phone,
            "city": l.city,
            "category": l.interested_category,
            "budget": l.budget,
            "requirement": l.requirement,
            "score": l.score,
            "status": l.qualification_status,
            "updated_at": str(l.updated_at)
        }
        for l in leads
    ]


@app.get("/appointments")
def list_appointments(db: Session = Depends(get_db)):
    """Retrieve all scheduled store visits and sales consultations."""
    appts = db.query(Appointment).order_by(Appointment.appointment_date.asc()).all()
    return [
        {
            "appointment_id": a.appointment_id,
            "customer_name": a.customer_name,
            "customer_email": a.customer_email,
            "date": a.appointment_date,
            "time": a.appointment_time,
            "type": a.appointment_type,
            "product": a.interested_product,
            "city": a.city,
            "status": a.status,
            "notes": a.notes
        }
        for a in appts
    ]


@app.get("/insights")
def get_sales_insights(db: Session = Depends(get_db)):
    """Retrieve aggregated executive sales analytics."""
    leads = db.query(Lead).all()
    appts = db.query(Appointment).all()
    calls = db.query(Call).all()

    total_leads = len(leads)
    hot_leads = sum(1 for l in leads if l.qualification_status == "HOT")
    warm_leads = sum(1 for l in leads if l.qualification_status == "WARM")
    cold_leads = sum(1 for l in leads if l.qualification_status == "COLD")
    avg_score = round(sum(l.score for l in leads) / total_leads, 1) if total_leads else 0

    return {
        "total_calls": len(calls),
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "appointments_booked": len(appts),
        "average_lead_score": avg_score
    }


@app.post("/crm/webhook")
def crm_webhook(payload: WebhookPayload):
    """Mock webhook receiver for outbound CRM sync events (HubSpot / Zoho / Salesforce)."""
    return {
        "status": "received",
        "event": payload.event,
        "synced_at": time.time(),
        "mock_destination": "ElectroMart India Salesforce CRM Sandbox"
    }
