"""
TechNova Solutions — Database Setup and Sample Data Seeding
Initializes SQLite and seeds the dashboard with realistic demo data.
"""
import os
import datetime
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import Base

# TechNova uses a separate DB file so it doesn't conflict with the existing project
TN_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "technova.db")
TN_DATABASE_URL = f"sqlite:///{TN_DB_PATH}"

tn_engine = create_engine(TN_DATABASE_URL, connect_args={"check_same_thread": False})
TNSession = sessionmaker(autocommit=False, autoflush=False, bind=tn_engine)


def get_tn_db():
    """Yield a TechNova database session."""
    db = TNSession()
    try:
        yield db
    finally:
        db.close()


def init_tn_db():
    """Create all TechNova tables."""
    import database.technova_models  # Ensure models are loaded
    Base.metadata.create_all(bind=tn_engine)


def seed_demo_data():
    """
    Seed realistic demo data so the dashboard is never empty.
    Only runs if the database is fresh (< 5 leads exist).
    """
    from database.technova_models import TNLead, TNConversation, TNMessage, TNAppointment, TNCallReport

    db = TNSession()
    try:
        if db.query(TNLead).count() >= 5:
            return  # Already seeded

        # --- Sample Leads ---
        leads_data = [
            {"name": "Priya Sharma", "email": "priya@retailco.in", "phone": "+91-9876543210",
             "company": "RetailCo India", "requirements": "Need CRM for 30-person sales team",
             "budget": "$299/month", "timeline": "This quarter", "interested_product": "TechNova CRM Suite",
             "lead_status": "Hot", "score": 85},
            {"name": "James Miller", "email": "james.miller@acmemfg.com", "phone": "+1-555-234-5678",
             "company": "Acme Manufacturing", "requirements": "ERP with inventory management",
             "budget": "Custom Enterprise", "timeline": "Next 6 months", "interested_product": "TechNova ERP Pro",
             "lead_status": "Hot", "score": 78},
            {"name": "Ananya Verma", "email": "ananya@healthplus.in", "phone": "+91-9123456789",
             "company": "HealthPlus Clinics", "requirements": "Analytics for patient data reporting",
             "budget": "$299/month", "timeline": "Next 3 months", "interested_product": "TechNova Analytics Hub",
             "lead_status": "Warm", "score": 60},
            {"name": "Robert Chen", "email": "robert.chen@techstart.io", "phone": "+1-555-987-6543",
             "company": "TechStart.io", "requirements": "Looking for affordable CRM for 5 users",
             "budget": "$99/month", "timeline": "Exploring options", "interested_product": "TechNova CRM Suite",
             "lead_status": "Warm", "score": 45},
            {"name": "Fatima Al-Hassan", "email": "fatima@globalconsult.ae", "phone": "+971-50-123-4567",
             "company": "Global Consult AE", "requirements": "Just browsing, need more info",
             "budget": "Not decided", "timeline": "No timeline", "interested_product": "Full Suite",
             "lead_status": "Cold", "score": 20},
            {"name": "Vikram Nair", "email": "vikram@ecomstore.in", "phone": "+91-8800112233",
             "company": "EcomStore India", "requirements": "CRM + Analytics integration for e-commerce",
             "budget": "$299/month", "timeline": "Immediate", "interested_product": "TechNova CRM Suite",
             "lead_status": "Hot", "score": 92},
        ]

        lead_objects = []
        base_date = datetime.datetime.utcnow() - datetime.timedelta(days=14)
        for i, ld in enumerate(leads_data):
            lead = TNLead(
                **ld,
                created_at=base_date + datetime.timedelta(days=i * 2),
                updated_at=base_date + datetime.timedelta(days=i * 2 + 1)
            )
            db.add(lead)
            lead_objects.append(lead)
        db.flush()

        # --- Sample Appointments ---
        appt_data = [
            {"customer_name": "Priya Sharma", "customer_email": "priya@retailco.in",
             "appointment_date": "2026-11-28", "appointment_time": "11:00 AM",
             "product_interest": "TechNova CRM Suite", "notes": "30-day trial requested", "status": "Scheduled"},
            {"customer_name": "James Miller", "customer_email": "james.miller@acmemfg.com",
             "appointment_date": "2026-11-29", "appointment_time": "3:00 PM",
             "product_interest": "TechNova ERP Pro", "notes": "Full enterprise demo", "status": "Scheduled"},
            {"customer_name": "Vikram Nair", "customer_email": "vikram@ecomstore.in",
             "appointment_date": "2026-11-26", "appointment_time": "2:00 PM",
             "product_interest": "TechNova CRM Suite", "notes": "Demo + pricing discussion", "status": "Scheduled"},
            {"customer_name": "Ananya Verma", "customer_email": "ananya@healthplus.in",
             "appointment_date": "2026-11-25", "appointment_time": "10:00 AM",
             "product_interest": "TechNova Analytics Hub", "notes": "Completed", "status": "Completed"},
        ]
        for i, ad in enumerate(appt_data):
            appt = TNAppointment(
                lead_id=lead_objects[i % len(lead_objects)].id,
                **ad,
                created_at=base_date + datetime.timedelta(days=i)
            )
            db.add(appt)

        # --- Sample Call Reports ---
        report_data = [
            {"lead_name": "Priya Sharma", "summary": "Customer interested in TechNova CRM for retail sales team of 30 people.",
             "requirements": "CRM with pipeline tracking and mobile app", "products_discussed": "TechNova CRM Suite",
             "sentiment": "Positive", "lead_status": "Hot",
             "next_action": "Send Professional plan proposal and book technical demo"},
            {"lead_name": "James Miller", "summary": "Manufacturing company needs ERP with inventory and HR modules.",
             "requirements": "Full ERP with multi-warehouse support", "products_discussed": "TechNova ERP Pro",
             "sentiment": "Positive", "lead_status": "Hot",
             "next_action": "Schedule on-site demonstration with implementation team"},
            {"lead_name": "Ananya Verma", "summary": "Healthcare analytics dashboard needed for 5 clinic locations.",
             "requirements": "Real-time patient flow reporting", "products_discussed": "TechNova Analytics Hub",
             "sentiment": "Neutral", "lead_status": "Warm",
             "next_action": "Share HIPAA compliance documentation and Analytics Hub brochure"},
        ]
        for rd in report_data:
            report = TNCallReport(**rd, created_at=base_date + datetime.timedelta(days=random.randint(1, 10)))
            db.add(report)

        db.commit()
        print("✅ TechNova demo data seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Seeding skipped: {e}")
    finally:
        db.close()
