"""
TechNova Solutions — FastAPI Application
Endpoints for chat, lead management, appointments, call summaries, and webhooks.
Run with: python -m uvicorn backend.technova_main:app --port 8001 --reload
"""
import os
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.technova_db import get_tn_db, init_tn_db, seed_demo_data
from database.technova_models import TNLead, TNConversation, TNMessage, TNAppointment, TNCallReport
from backend.technova_agent import chat, summarize_conversation, is_demo_mode, AGENT_NAME, COMPANY_NAME
from backend.technova_appointment import book_appointment_in_db

app = FastAPI(
    title="TechNova Solutions — AI Sales Agent API",
    version="1.0.0",
    description="Autonomous Sales Voice Agent API: Conversations, Lead Qualification, Appointments & CRM."
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
    init_tn_db()
    seed_demo_data()


# --- Pydantic Schemas ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    history: Optional[List[Dict[str, Any]]] = []


class AppointmentRequest(BaseModel):
    lead_id: Optional[int] = None
    customer_name: str
    customer_email: str
    appointment_date: str
    appointment_time: str
    product_interest: Optional[str] = "TechNova CRM Suite"
    notes: Optional[str] = ""


class LeadCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    requirements: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    interested_product: Optional[str] = None
    lead_status: Optional[str] = "Cold"
    score: Optional[int] = 0


class WebhookPayload(BaseModel):
    event: str
    data: Dict[str, Any]


# --- Endpoints ---
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "company": COMPANY_NAME,
        "agent": AGENT_NAME,
        "mode": "Demo Mode" if is_demo_mode() else "OpenAI Mode",
        "timestamp": time.time()
    }


@app.post("/chat")
def handle_chat(payload: ChatRequest):
    """Process a sales message through RAG, Agent, Sentiment and Qualification."""
    result = chat(user_message=payload.message, history=payload.history)
    return result


@app.get("/leads")
def list_leads(
    status: Optional[str] = Query(None, description="Filter by Hot, Warm, Cold"),
    db: Session = Depends(get_tn_db)
):
    """Retrieve all leads with optional status filter."""
    query = db.query(TNLead)
    if status:
        query = query.filter(TNLead.lead_status.ilike(status))
    leads = query.order_by(TNLead.updated_at.desc()).all()
    return [
        {
            "id": l.id,
            "name": l.name,
            "email": l.email,
            "phone": l.phone,
            "company": l.company,
            "requirements": l.requirements,
            "budget": l.budget,
            "timeline": l.timeline,
            "interested_product": l.interested_product,
            "lead_status": l.lead_status,
            "score": l.score,
            "created_at": str(l.created_at) if l.created_at else None
        }
        for l in leads
    ]


@app.post("/leads")
def create_lead(payload: LeadCreate, db: Session = Depends(get_tn_db)):
    """Add a lead to the database."""
    lead = TNLead(**payload.dict())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return {"status": "success", "lead_id": lead.id}


@app.get("/appointments")
def list_appointments(db: Session = Depends(get_tn_db)):
    """Retrieve all demo appointments."""
    appts = db.query(TNAppointment).order_by(TNAppointment.appointment_date.asc()).all()
    return [
        {
            "id": a.id,
            "lead_id": a.lead_id,
            "customer_name": a.customer_name,
            "customer_email": a.customer_email,
            "appointment_date": a.appointment_date,
            "appointment_time": a.appointment_time,
            "product_interest": a.product_interest,
            "status": a.status,
            "notes": a.notes
        }
        for a in appts
    ]


@app.post("/appointments")
def book_appointment(payload: AppointmentRequest, db: Session = Depends(get_tn_db)):
    """Book a new demo appointment with conflict checking."""
    success, msg = book_appointment_in_db(
        db=db,
        lead_id=payload.lead_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time,
        product_interest=payload.product_interest or "TechNova CRM Suite",
        notes=payload.notes or ""
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg}


@app.get("/reports")
def list_call_reports(db: Session = Depends(get_tn_db)):
    """Retrieve call summaries and sentiment reports."""
    reports = db.query(TNCallReport).order_by(TNCallReport.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "lead_name": r.lead_name,
            "summary": r.summary,
            "requirements": r.requirements,
            "products_discussed": r.products_discussed,
            "sentiment": r.sentiment,
            "lead_status": r.lead_status,
            "next_action": r.next_action,
            "created_at": str(r.created_at) if r.created_at else None
        }
        for r in reports
    ]


@app.post("/crm/webhook")
def crm_webhook(payload: WebhookPayload):
    """Mock webhook receiver for outbound CRM sync events (HubSpot / Salesforce)."""
    return {
        "status": "received",
        "event": payload.event,
        "synced_at": time.time(),
        "mock_destination": "Salesforce CRM Sandbox"
    }
