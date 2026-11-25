"""
ElectroMart India — SQLAlchemy Database Models
Stores Customers, Leads, Calls, Messages, Appointments, Recommended Products, and Call Summaries.
"""
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class Customer(Base):
    """Customer profile record."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(128), index=True, nullable=True)
    phone = Column(String(32), nullable=True)
    city = Column(String(64), nullable=True)
    customer_type = Column(String(64), default="Retail Prospect")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    leads = relationship("Lead", back_populates="customer")


class Lead(Base):
    """Lead qualification opportunity record."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(32), ForeignKey("customers.customer_id"), nullable=True)
    call_id = Column(String(64), index=True, nullable=True)
    name = Column(String(128), nullable=True)
    email = Column(String(128), index=True, nullable=True)
    phone = Column(String(32), nullable=True)
    city = Column(String(64), nullable=True)
    interested_category = Column(String(64), nullable=True)
    budget = Column(String(64), nullable=True)
    requirement = Column(Text, nullable=True)
    purchase_timeline = Column(String(64), nullable=True)
    purchase_intent = Column(String(32), default="Exploring")
    score = Column(Integer, default=0)
    qualification_status = Column(String(16), default="COLD")  # HOT, WARM, COLD
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="leads")


class Call(Base):
    """Voice & conversational call session."""
    __tablename__ = "calls"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(32), nullable=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    language = Column(String(16), default="en")
    summary = Column(Text, nullable=True)
    final_sentiment = Column(String(16), nullable=True)
    final_score = Column(Integer, default=0)

    messages = relationship("Message", back_populates="call", cascade="all, delete-orphan")


class Message(Base):
    """Individual dialogue turn in a call."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(64), ForeignKey("calls.id"), nullable=False)
    sender = Column(String(16), nullable=False)  # 'user' or 'agent'
    text = Column(Text, nullable=False)
    sentiment_label = Column(String(16), default="neutral")
    sentiment_score = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    call = relationship("Call", back_populates="messages")


class Appointment(Base):
    """Store visit or sales consultation appointment."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String(32), unique=True, index=True, nullable=True)
    customer_name = Column(String(128), nullable=False)
    customer_email = Column(String(128), nullable=False)
    customer_phone = Column(String(32), nullable=True)
    appointment_date = Column(String(32), nullable=False)  # YYYY-MM-DD
    appointment_time = Column(String(16), nullable=False)  # HH:MM AM/PM
    appointment_type = Column(String(64), default="Store Visit")
    interested_product = Column(String(128), nullable=True)
    city = Column(String(64), default="Mumbai")
    status = Column(String(16), default="Confirmed")  # Confirmed, Scheduled, Completed, Cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class RecommendedProduct(Base):
    """Product recommended during a sales interaction."""
    __tablename__ = "recommended_products"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(64), index=True, nullable=False)
    product_id = Column(String(32), nullable=False)
    product_name = Column(String(128), nullable=False)
    price_inr = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class CallSummary(Base):
    """Structured executive summary of a completed sales interaction."""
    __tablename__ = "call_summaries"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_name = Column(String(128), nullable=True)
    requirements = Column(Text, nullable=True)
    category = Column(String(64), nullable=True)
    budget = Column(String(64), nullable=True)
    recommended_products = Column(Text, nullable=True)
    key_questions = Column(Text, nullable=True)
    objections = Column(Text, nullable=True)
    sentiment = Column(String(16), nullable=True)
    lead_score = Column(Integer, default=0)
    lead_status = Column(String(16), default="COLD")
    appointment_details = Column(Text, nullable=True)
    next_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
