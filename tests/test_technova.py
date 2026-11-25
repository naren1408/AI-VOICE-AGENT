"""
Test Suite for TechNova Solutions AI Sales Agent.
Validates:
1. BANT Lead Scoring & Status classification.
2. Sentiment analysis and escalation trigger.
3. RAG retrieval using TF-IDF.
4. Demo appointment scheduling & duplicate booking prevention.
"""
import pytest
from backend.technova_leads import score_lead, extract_lead_info
from backend.technova_sentiment import analyze_sentiment, should_escalate
from backend.technova_rag import TechNovaRAG
from backend.technova_appointment import validate_appointment, book_appointment_in_db
from database.technova_db import init_tn_db, TNSession
from database.technova_models import TNAppointment


@pytest.fixture(autouse=True)
def setup_db():
    init_tn_db()


def test_technova_hot_lead_scoring():
    lead_info = {
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.com",
        "phone": "+1-555-0199",
        "company": "Cyberdyne Systems",
        "budget": "$299/month",
        "timeline": "This month",
        "requirements": "Need full CRM with sales pipeline tracking"
    }
    score, status = score_lead(lead_info)
    assert score >= 70
    assert status == "Hot"


def test_technova_cold_lead_scoring():
    lead_info = {
        "name": "",
        "email": "",
        "phone": "",
        "company": "",
        "budget": "",
        "timeline": "",
        "requirements": "Just looking around"
    }
    score, status = score_lead(lead_info)
    assert score < 40
    assert status == "Cold"


def test_technova_sentiment_positive():
    label, score = analyze_sentiment("I really love the analytics features, it is wonderful!")
    assert label == "Positive"
    assert score > 0.0


def test_technova_sentiment_negative_and_escalation():
    label, score = analyze_sentiment("This pricing is terrible and awful, I am extremely frustrated.")
    assert label == "Negative"
    assert score < 0.0
    assert should_escalate(score) is True


def test_technova_rag_retrieval():
    rag = TechNovaRAG()
    results = rag.retrieve("What are the pricing tiers?", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "99" in top_chunk or "299" in top_chunk or "Starter" in top_chunk or "Professional" in top_chunk


def test_technova_appointment_booking_and_conflict():
    db = TNSession()
    try:
        # Clear existing test appointment for this slot
        db.query(TNAppointment).filter(
            TNAppointment.customer_email == "alice@techcorp.com",
            TNAppointment.appointment_date == "2026-12-15",
            TNAppointment.appointment_time == "11:00 AM"
        ).delete()
        db.commit()

        # Book first time (2026-12-15 is a Tuesday)
        success1, msg1 = book_appointment_in_db(
            db=db,
            lead_id=None,
            name="Alice Smith",
            email="alice@techcorp.com",
            date_str="2026-12-15",
            time_str="11:00 AM",
            product="TechNova CRM Suite",
            notes="Testing booking"
        )
        assert success1 is True

        # Attempt duplicate booking for same customer, date, time
        success2, msg2 = book_appointment_in_db(
            db=db,
            lead_id=None,
            name="Alice Smith",
            email="alice@techcorp.com",
            date_str="2026-12-15",
            time_str="11:00 AM",
            product="TechNova CRM Suite",
            notes="Duplicate attempt"
        )
        assert success2 is False
        assert "already have an appointment" in msg2.lower()
    finally:
        db.close()
