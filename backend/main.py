import os
import uuid
import time
import requests
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db, init_db
from database.models import Lead, Call, Message, Appointment
from backend.ai_agent import execute_sales_turn, generate_call_summary, is_demo_mode
from backend.speech_to_text import transcribe_audio_gemini
from backend.text_to_speech import text_to_speech

# Initialize FastAPI application
app = FastAPI(
    title="CloudScale AI - Autonomous Sales Voice Agent API",
    version="1.0.0",
    description="MVP Voice & Conversational Sales Agent with RAG, Lead Scoring, and Calendar Booking."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema on startup
@app.on_event("startup")
def on_startup():
    init_db()


# --- Pydantic Schemas ---
class StartCallResponse(BaseModel):
    call_id: str
    message: str
    mode: str


class TextTurnRequest(BaseModel):
    text: str
    language: Optional[str] = "en"


class WebhookPayload(BaseModel):
    event: str
    lead_id: Optional[int] = None
    email: Optional[str] = None
    name: Optional[str] = None
    score: Optional[int] = 0
    status: Optional[str] = "COLD"


# --- API Endpoints ---
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "mode": "Demo Mode" if is_demo_mode() else "Gemini Mode"
    }


@app.post("/call/start", response_model=StartCallResponse)
def start_call(db: Session = Depends(get_db)):
    """Initialize a new customer call session with a unique call ID."""
    call_id = str(uuid.uuid4())[:8]
    new_call = Call(id=call_id)
    db.add(new_call)
    db.commit()
    mode = "Demo Mode" if is_demo_mode() else "Gemini Mode"
    return StartCallResponse(
        call_id=call_id,
        message=f"Call session {call_id} started successfully in {mode}.",
        mode=mode
    )


@app.post("/call/{call_id}/text")
def send_text_turn(call_id: str, payload: TextTurnRequest):
    """Process a conversational text turn through RAG, Agent, Qualification and DB."""
    result = execute_sales_turn(
        call_id=call_id,
        user_input=payload.text,
        language=payload.language or "en"
    )
    return result


@app.post("/call/{call_id}/audio")
async def send_audio_turn(call_id: str, audio: UploadFile = File(...)):
    """Transcribe inbound audio, run conversational turn, synthesize voice reply."""
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    temp_input_path = os.path.join(temp_dir, f"{call_id}_in.wav")
    temp_output_path = os.path.join(temp_dir, f"{call_id}_out.mp3")

    with open(temp_input_path, "wb") as f:
        f.write(await audio.read())

    # Transcribe audio
    transcript, lang = transcribe_audio_gemini(temp_input_path)

    # Execute sales turn
    result = execute_sales_turn(call_id=call_id, user_input=transcript, language=lang)

    # Synthesize reply with edge-tts
    text_to_speech(result["reply"], temp_output_path, language=lang)
    result["audio_url"] = f"/static/audio/{call_id}_out.mp3"
    result["transcript"] = transcript
    return result


@app.post("/call/{call_id}/end")
def end_call(call_id: str):
    """End the call, generate structured summary, and push qualified lead to CRM."""
    summary_data = generate_call_summary(call_id)

    # Push to CRM webhook if configured
    crm_url = os.getenv("CRM_WEBHOOK_URL", "http://localhost:8000/crm/webhook")
    try:
        requests.post(
            crm_url,
            json={
                "event": "call_ended",
                "call_id": call_id,
                "summary": summary_data.get("summary"),
                "score": summary_data.get("score"),
                "status": summary_data.get("status")
            },
            timeout=2.0
        )
    except Exception:
        # Graceful non-blocking fallback if webhook is offline
        pass

    return summary_data


@app.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    """Retrieve all leads from SQLite CRM."""
    leads = db.query(Lead).order_by(Lead.updated_at.desc()).all()
    return leads


@app.get("/appointments")
def get_appointments(db: Session = Depends(get_db)):
    """Retrieve all scheduled appointments."""
    appts = db.query(Appointment).order_by(Appointment.slot_time.asc()).all()
    return appts


@app.get("/insights")
def get_insights(db: Session = Depends(get_db)):
    """Compute aggregate analytics: total calls, demos booked, conversion %, average score, sentiment."""
    total_calls = db.query(Call).count()
    demos_booked = db.query(Appointment).filter(Appointment.status == "CONFIRMED").count()
    leads = db.query(Lead).all()
    avg_score = round(sum(l.score for l in leads) / len(leads), 1) if leads else 0.0
    conversion_rate = round((demos_booked / total_calls * 100), 1) if total_calls > 0 else 0.0

    # Sentiment distribution
    messages = db.query(Message).filter(Message.sender == "user").all()
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for m in messages:
        lbl = m.sentiment_label or "neutral"
        if lbl in sentiment_counts:
            sentiment_counts[lbl] += 1

    return {
        "total_calls": total_calls,
        "demos_booked": demos_booked,
        "conversion_rate": conversion_rate,
        "average_lead_score": avg_score,
        "sentiment_distribution": sentiment_counts,
        "top_questions": [
            "What are your pricing tiers?",
            "Can I optimize Kubernetes compute waste?",
            "How does CloudScale AI compare with AWS native tools?",
            "Is there a 14-day free trial?"
        ]
    }


@app.post("/crm/webhook")
def crm_webhook(payload: dict):
    """Mock CRM receiver endpoint (HubSpot / Zoho simulation)."""
    return {
        "status": "success",
        "received_payload": payload,
        "message": "CRM lead successfully synchronized."
    }
