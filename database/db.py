"""
ElectroMart India — Database Configuration & Data Seeder
SQLite with SQLAlchemy ORM.
Automatically seeds from data/ on startup if tables are fresh.
"""
import os
import datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(DB_DIR)
DB_PATH = os.path.join(DB_DIR, "electromart.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables in the SQLite database and seed initial synthetic records."""
    import database.models  # ensure models are registered
    from sqlalchemy import text
    Base.metadata.create_all(bind=engine)

    # SQLite schema migration for added columns
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(appointments)")).fetchall()
            col_names = [r[1] for r in res]
            if "location" not in col_names:
                conn.execute(text("ALTER TABLE appointments ADD COLUMN location VARCHAR(256)"))
            if "updated_at" not in col_names:
                conn.execute(text("ALTER TABLE appointments ADD COLUMN updated_at DATETIME"))
            conn.commit()
        except Exception as e:
            pass

    seed_initial_data()


def seed_initial_data():
    """Seed sample customers, leads, and appointments from data/ directory if database is empty."""
    from database.models import Customer, Lead, Appointment

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Customer).count() >= 5:
            return

        data_dir = os.path.join(PROJECT_DIR, "data")
        cust_csv = os.path.join(data_dir, "customers.csv")
        leads_csv = os.path.join(data_dir, "sample_leads.csv")
        appts_csv = os.path.join(data_dir, "appointments.csv")

        # 1. Customers
        if os.path.exists(cust_csv):
            df_c = pd.read_csv(cust_csv)
            for _, r in df_c.iterrows():
                if not db.query(Customer).filter(Customer.customer_id == r["customer_id"]).first():
                    db.add(Customer(
                        customer_id=r["customer_id"],
                        name=r["name"],
                        email=r["email"],
                        phone=r["phone"],
                        city=r["city"],
                        customer_type=r["customer_type"]
                    ))
            db.flush()

        # 2. Leads
        if os.path.exists(leads_csv):
            df_l = pd.read_csv(leads_csv)
            cust_dict = {c.customer_id: c for c in db.query(Customer).all()}
            for _, r in df_l.iterrows():
                cid = r["customer_id"]
                cust = cust_dict.get(cid)
                db.add(Lead(
                    customer_id=cid,
                    name=cust.name if cust else "Prospective Buyer",
                    email=cust.email if cust else None,
                    phone=cust.phone if cust else None,
                    city=cust.city if cust else "Mumbai",
                    interested_category=r["interested_category"],
                    budget=r["budget"],
                    requirement=r["requirement"],
                    purchase_timeline=r["purchase_timeline"],
                    purchase_intent="High" if r["lead_status"] == "HOT" else "Medium",
                    score=int(r["lead_score"]),
                    qualification_status=r["lead_status"]
                ))
            db.flush()

        # 3. Appointments
        if os.path.exists(appts_csv):
            df_a = pd.read_csv(appts_csv)
            for _, r in df_a.iterrows():
                if not db.query(Appointment).filter(Appointment.appointment_id == r["appointment_id"]).first():
                    db.add(Appointment(
                        appointment_id=r["appointment_id"],
                        customer_name=r["customer_name"],
                        customer_email=r["customer_email"],
                        customer_phone=r["customer_phone"],
                        appointment_date=r["date"],
                        appointment_time=r["time"],
                        appointment_type=r["appointment_type"],
                        interested_product=r["interested_product"],
                        city=r["city"],
                        status=r["status"],
                        notes=r["notes"]
                    ))
            db.flush()

        db.commit()
        print("✅ ElectroMart India sample data seeded successfully into SQLite.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Seeding skipped: {e}")
    finally:
        db.close()
