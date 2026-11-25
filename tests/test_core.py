"""
ElectroMart India — Comprehensive Core Test Suite
Validates:
1. Product dataset loading and filtering by budget.
2. Product recommendation engine accuracy.
3. BANT Lead qualification scoring & bands (HOT, WARM, COLD).
4. Sentiment analysis and escalation detection.
5. TF-IDF RAG knowledge retrieval and cosine scoring.
6. Appointment booking, duplicate slot prevention, and business hours validation.
7. CSV and JSON dataset consistency.
8. SQLite database persistence.
"""
import os
import json
import datetime
import pytest
import pandas as pd

from database.db import init_db, SessionLocal
from database.models import Customer, Lead, Appointment, Call
from backend.product_recommendation import load_products_df, parse_budget_from_text, recommend_products
from backend.lead_qualification import extract_lead_from_conversation, LEAD_SCORING_WEIGHTS
from backend.sentiment import analyze_sentiment, should_escalate
from backend.rag import ElectroMartRAG
from backend.appointment import parse_natural_datetime, validate_appointment_slot, book_appointment_in_db, generate_ics_content


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema and synthetic records exist before tests."""
    init_db()


def test_products_csv_loading_and_filtering():
    """Verify products.csv has at least 25 items across 4 categories and budget filtering works."""
    df = load_products_df()
    assert not df.empty
    assert len(df) >= 25
    categories = set(df["category"].unique())
    assert "Laptops" in categories
    assert "Smartphones" in categories
    assert "Tablets" in categories
    assert "Accessories" in categories

    # Budget filter: products under 50,000
    under_50k = df[df["price_inr"] <= 50000]
    assert len(under_50k) > 0
    assert all(under_50k["price_inr"] <= 50000)


def test_parse_budget_from_text():
    """Test natural language budget extraction."""
    assert parse_budget_from_text("I need a laptop under ₹70,000") == 70000
    assert parse_budget_from_text("My budget is 35k") == 35000
    assert parse_budget_from_text("Looking around 1 lakh") == 100000
    assert parse_budget_from_text("Price under 25000 inr") == 25000


def test_product_recommendation_programming_laptop():
    """Verify CodeMaster Pro 15 or DevForge is recommended for coding within 70k."""
    recs = recommend_products("I need a laptop under 70000 for programming and python", max_results=3)
    assert len(recs) > 0
    rec_names = [r["product_name"] for r in recs]
    assert any("CodeMaster" in name or "ZenithBook" in name for name in rec_names)
    assert recs[0]["price_inr"] <= 70000


def test_product_recommendation_student_laptop():
    """Verify budget student laptop recommendation."""
    recs = recommend_products("I am a student looking for a laptop under 35k", max_results=2)
    assert len(recs) > 0
    assert recs[0]["price_inr"] <= 35000
    assert "VoltBook" in recs[0]["product_name"] or "EcoBook" in recs[0]["product_name"]


def test_lead_scoring_hot():
    """Test that customer with clear need, budget, urgent timeline, contact, and intent scores HOT (>=70)."""
    text = (
        "My name is Priya Patel. My email is priya@example.com and phone is +91-98765-43210. "
        "I need a laptop for programming with 16GB RAM under ₹70,000. "
        "I want to buy immediately tomorrow and visit your store."
    )
    lead = extract_lead_from_conversation(text)
    assert lead.score >= 70
    assert lead.status == "HOT"
    assert lead.name == "Priya Patel"
    assert lead.email == "priya@example.com"


def test_lead_scoring_warm_and_cold():
    """Test WARM (40-69) and COLD (<40) lead classifications."""
    # Warm lead: has budget and requirement, but no email or immediate timeline
    warm_text = "I am looking for a camera smartphone under 35,000."
    lead_warm = extract_lead_from_conversation(warm_text)
    assert 40 <= lead_warm.score < 70
    assert lead_warm.status == "WARM"

    # Cold lead: vague browsing
    cold_text = "Just checking prices."
    lead_cold = extract_lead_from_conversation(cold_text)
    assert lead_cold.score < 40
    assert lead_cold.status == "COLD"


def test_sentiment_analysis_accuracy():
    """Verify positive, neutral, and negative sentiment detection without false positives."""
    # Positive
    label_p, score_p = analyze_sentiment("Great product! I love the display and helpful customer service.")
    assert label_p == "positive"
    assert score_p > 0.0

    # Negative
    label_n, score_n = analyze_sentiment("This price is terrible and overpriced, very frustrating service.")
    assert label_n == "negative"
    assert score_n < 0.0
    assert should_escalate(score_n) is True

    # Neutral (critical test: 'innovative', 'know', or 'laptop' must NOT trigger negative 'no')
    label_neu, score_neu = analyze_sentiment("Hello, I want to know about your laptop models.")
    assert label_neu == "neutral"
    assert score_neu == 0.0


def test_rag_retrieval_and_cosine_scoring():
    """Verify TF-IDF RAG retrieves accurate context chunks."""
    rag = ElectroMartRAG()
    results = rag.retrieve("What is the warranty policy on laptops?", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert score > 0.0
    assert "warranty" in top_chunk.lower() or "policy" in top_chunk.lower()


def test_appointment_booking_and_double_booking_prevention():
    """Test appointment booking, slot verification, and duplicate booking prevention."""
    db = SessionLocal()
    try:
        test_email = "test.shopper@example.com"
        test_date = datetime.date.today() + datetime.timedelta(days=3)
        test_time = "04:00 PM"

        # Clear existing test bookings
        db.query(Appointment).filter(
            Appointment.customer_email == test_email,
            Appointment.appointment_date == test_date.strftime("%Y-%m-%d")
        ).delete()
        db.commit()

        # 1. Book first appointment
        ok1, msg1, appt1 = book_appointment_in_db(
            db=db,
            customer_name="Test Shopper",
            customer_email=test_email,
            customer_phone="+91-99999-88888",
            date_val=test_date,
            time_str=test_time,
            appointment_type="Store Visit",
            interested_product="CodeMaster Pro 15",
            city="Bengaluru"
        )
        assert ok1 is True
        assert appt1 is not None
        assert "confirmed" in msg1.lower()

        # 2. Attempt duplicate booking for same customer and slot
        ok2, msg2, appt2 = book_appointment_in_db(
            db=db,
            customer_name="Test Shopper",
            customer_email=test_email,
            customer_phone="+91-99999-88888",
            date_val=test_date,
            time_str=test_time,
            appointment_type="Store Visit",
            interested_product="CodeMaster Pro 15",
            city="Bengaluru"
        )
        assert ok2 is False
        assert "already have a confirmed appointment" in msg2.lower()
        assert appt2 is None

    finally:
        db.close()


def test_appointment_hours_validation():
    """Verify that appointments outside operating hours (10 AM to 8:30 PM) are rejected."""
    today = datetime.date.today()
    # 02:00 AM is outside operating hours
    valid, reason = validate_appointment_slot(today, "02:00 AM")
    assert valid is False
    assert "operating hours" in reason.lower()

    # 04:00 PM is valid
    valid_pm, _ = validate_appointment_slot(today, "04:00 PM")
    assert valid_pm is True


def test_ics_generation():
    """Verify RFC 5545 calendar file content structure."""
    target_date = datetime.date(2026, 12, 1)
    ics = generate_ics_content("Priya Patel", target_date, "04:00 PM", "CodeMaster Pro 15")
    assert "BEGIN:VCALENDAR" in ics
    assert "END:VCALENDAR" in ics
    assert "SUMMARY:ElectroMart India Store Demo: CodeMaster Pro 15" in ics


def test_synthetic_datasets_consistency():
    """Verify consistency between products.csv, customers.csv, leads.csv, and faqs.json."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    # Products >= 25
    df_p = pd.read_csv(os.path.join(data_dir, "products.csv"))
    assert len(df_p) >= 25

    # Customers >= 20
    df_c = pd.read_csv(os.path.join(data_dir, "customers.csv"))
    assert len(df_c) >= 20

    # Leads >= 15
    df_l = pd.read_csv(os.path.join(data_dir, "sample_leads.csv"))
    assert len(df_l) >= 15

    # Check foreign keys from leads to customers
    cust_ids = set(df_c["customer_id"].unique())
    lead_cust_ids = set(df_l["customer_id"].unique())
    assert lead_cust_ids.issubset(cust_ids)

    # FAQs >= 25
    with open(os.path.join(data_dir, "faqs.json"), "r", encoding="utf-8") as f:
        faqs = json.load(f)
    assert len(faqs) >= 25


def test_database_persistence():
    """Verify that customer and call records persist in SQLite."""
    db = SessionLocal()
    try:
        call_id = "TEST-CALL-001"
        db.query(Call).filter(Call.id == call_id).delete()
        db.commit()

        call = Call(id=call_id, language="en", summary="Test sales call")
        db.add(call)
        db.commit()

        fetched = db.query(Call).filter(Call.id == call_id).first()
        assert fetched is not None
        assert fetched.summary == "Test sales call"
    finally:
        db.close()


def test_conversational_edge_cases():
    """Verify conversational edge cases from live testing."""
    from backend.ai_agent import execute_sales_turn

    # 1. Introduction + Category Inquiry
    r1 = execute_sales_turn("TEST-T1", "my name is Sai Narayan and I need to know what categories are present and can you introduce yourself")
    assert "Sai Narayan" in r1["reply"]
    assert "Laptops" in r1["reply"] and "Smartphones" in r1["reply"] and "Tablets" in r1["reply"]
    assert r1["booking"] is None

    # 2. Looking for tablets today (no false booking)
    r2 = execute_sales_turn("TEST-T2", "hello Anya I am silent and I am from Delhi and I am looking for tablets today")
    assert r2["booking"] is None
    assert r2["lead"]["interested_category"] == "Tablets"
    assert r2["lead"]["city"] == "Delhi"

    # 3. Catalog scope inquiry (more phones available)
    r3 = execute_sales_turn("TEST-T3", "there are only three phones available in this or there are more phones are available")
    assert "7 smartphones" in r3["reply"]

    # 4. Display available items (clean catalog overview, no SaaS trial text)
    r4 = execute_sales_turn("TEST-T4", "can you display the items that are available on this website")
    assert "25 top-rated electronics" in r4["reply"]
    assert "free trial" not in r4["reply"].lower()

    # 5. Gaming phone under 20000 (must recommend smartphones <= 20000, never a gaming laptop)
    r5 = execute_sales_turn("TEST-T5", "best gaming phone under 20000")
    assert "Pulse Velocity" in r5["reply"]
    assert "CyberPulse" not in r5["reply"]
    assert r5["lead"]["interested_category"] == "Smartphones"
    assert all(rec["price_inr"] <= 20000 for rec in r5["recommendations"])

    # 6. Telugu Conversation
    r6 = execute_sales_turn("TEST-TE", "నమస్కారం, నాకు కోడింగ్ కోసం లాప్‌టాప్ కావాలి")
    assert "నమస్కారం" in r6["reply"]
    assert r6["language"] == "te"

    # 7. Kannada Conversation
    r7 = execute_sales_turn("TEST-KN", "ನಮಸ್ಕಾರ, ನನಗೆ ಗೇಮಿಂಗ್ ಫೋನ್ ಬೇಕು")
    assert "ನಮಸ್ಕಾರ" in r7["reply"]
    assert r7["language"] == "kn"

    # 8. Appointment Request (must offer to schedule appointment, no raw FAQ dump)
    r8 = execute_sales_turn("TEST-APPT-REQ", "can I have an appointment for this product")
    assert "delighted to schedule a hands-on showroom appointment" in r8["reply"]
    assert "Category: Appointment" not in r8["reply"]

