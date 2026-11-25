import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db import Base
from database.models import Lead, Call, Message, Appointment
from backend.lead_qualification import (
    LeadQualificationData, calculate_lead_score, get_qualification_status, extract_lead_rule_based
)
from backend.sentiment import analyze_sentiment, requires_human_escalation
from backend.appointment import (
    check_availability, book_appointment, parse_natural_datetime, generate_ics_content
)
from backend.rag import SimpleRAG, cosine_similarity, keyword_overlap_score


@pytest.fixture
def test_db():
    """Create fresh in-memory SQLite database for test isolation."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# 1. LEAD SCORING & QUALIFICATION TESTS
# ==============================================================================
def test_lead_scoring_hot():
    """Verify lead scoring reaches HOT (>= 70) with budget, urgent timeline, decision maker, need."""
    lead = LeadQualificationData(
        name="Alex Mercer",
        email="alex@fintech.co",
        budget="$1,500/month",
        timeline="immediate",
        is_decision_maker=True,
        need="Need to reduce AWS EKS compute waste"
    )
    score = calculate_lead_score(lead)
    status = get_qualification_status(score)
    assert score >= 70, f"Expected HOT score >= 70, got {score}"
    assert status == "HOT"


def test_lead_scoring_warm_and_cold():
    """Verify WARM (>= 40) and COLD status boundaries."""
    warm_lead = LeadQualificationData(
        email="sarah@corp.com",
        budget="$500",
        need="Looking at cloud costs"
    )
    score_warm = calculate_lead_score(warm_lead)
    assert get_qualification_status(score_warm) in ["WARM", "HOT"]

    cold_lead = LeadQualificationData()
    score_cold = calculate_lead_score(cold_lead)
    assert score_cold == 0
    assert get_qualification_status(score_cold) == "COLD"


def test_rule_based_lead_extraction():
    """Verify regex extraction of email, name, and budget from conversation string."""
    text = "Hi, my name is David from Stripe. My email is david@stripe.com and our budget is $1,499/month. We need it this quarter."
    extracted = extract_lead_rule_based(text)
    assert extracted.email == "david@stripe.com"
    assert extracted.name == "David"
    assert "1,499" in extracted.budget
    assert extracted.timeline != ""


# ==============================================================================
# 2. SENTIMENT ANALYSIS & HUMAN ESCALATION TESTS
# ==============================================================================
def test_sentiment_positive():
    label, score = analyze_sentiment("This product is awesome and great, I love it!")
    assert label == "positive"
    assert score > 0


def test_sentiment_negative_and_escalation():
    label, score = analyze_sentiment("This is terrible, useless, and bad. Waste of money.")
    assert label == "negative"
    assert score < -0.5
    assert requires_human_escalation(score) is True


def test_sentiment_neutral():
    label, score = analyze_sentiment("Can you tell me about the features?")
    assert label == "neutral"
    assert score == 0.0


# ==============================================================================
# 3. APPOINTMENT BOOKING & DOUBLE-BOOKING TESTS
# ==============================================================================
def test_appointment_booking_and_double_booking(test_db):
    """Verify demo booking succeeds, and duplicate booking of identical slot is rejected."""
    # Find next available weekday at 14:00
    now = datetime.datetime.now()
    days_ahead = 1
    slot = datetime.datetime(now.year, now.month, now.day, 14, 0) + datetime.timedelta(days=days_ahead)
    while slot.weekday() >= 5:  # Skip weekends
        slot += datetime.timedelta(days=1)

    # First booking should succeed
    success1, msg1, appt1 = book_appointment(test_db, "Alice Smith", "alice@enterprise.com", slot, "call-123")
    assert success1 is True
    assert appt1 is not None

    # Second booking for the same slot must fail
    success2, msg2, appt2 = book_appointment(test_db, "Bob Jones", "bob@other.com", slot, "call-456")
    assert success2 is False
    assert "already booked" in msg2.lower()
    assert appt2 is None


def test_appointment_weekend_and_off_hours_rejection(test_db):
    """Verify weekend slots and outside working hours (9am-6pm) are rejected."""
    # Weekend test (Sunday)
    now = datetime.datetime.now()
    sunday_dt = now + datetime.timedelta(days=(6 - now.weekday()))
    sunday_slot = datetime.datetime(sunday_dt.year, sunday_dt.month, sunday_dt.day, 14, 0)
    avail, msg = check_availability(test_db, sunday_slot)
    assert avail is False
    assert "weekend" in msg.lower()

    # Off-hours test (8:00 AM or 19:00 PM)
    weekday_dt = now
    while weekday_dt.weekday() >= 5:
        weekday_dt += datetime.timedelta(days=1)
    off_slot = datetime.datetime(weekday_dt.year, weekday_dt.month, weekday_dt.day, 20, 0)
    avail_off, msg_off = check_availability(test_db, off_slot)
    assert avail_off is False
    assert "outside working hours" in msg_off.lower()


def test_ics_generation():
    """Verify iCalendar file string generation contains required VCALENDAR markers."""
    slot = datetime.datetime(2026, 12, 1, 15, 0)
    ics = generate_ics_content("Alice Smith", slot)
    assert "BEGIN:VCALENDAR" in ics
    assert "END:VCALENDAR" in ics
    assert "Alice Smith" in ics


# ==============================================================================
# 4. RAG RETRIEVAL & COSINE SIMILARITY TESTS
# ==============================================================================
def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(cosine_similarity(v1, v2), 0.01) == 1.0
    assert pytest.approx(cosine_similarity(v1, v3), 0.01) == 0.0


def test_rag_keyword_retrieval():
    rag = SimpleRAG()
    results = rag.retrieve("pricing tiers cost starter professional", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "pricing" in top_chunk.lower() or "tier" in top_chunk.lower() or "$499" in top_chunk
