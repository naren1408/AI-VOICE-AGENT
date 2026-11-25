"""
TechNova Solutions — SQLite Database Models
All models use SQLAlchemy ORM for clean, readable data access.
"""
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class TNLead(Base):
    """Stores TechNova lead qualification data."""
    __tablename__ = "tn_leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=True)
    email = Column(String(128), nullable=True, index=True)
    phone = Column(String(32), nullable=True)
    company = Column(String(128), nullable=True)
    requirements = Column(Text, nullable=True)
    budget = Column(String(64), nullable=True)
    timeline = Column(String(64), nullable=True)
    interested_product = Column(String(128), nullable=True)
    lead_status = Column(String(16), default="Cold")   # Hot, Warm, Cold
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    conversations = relationship("TNConversation", back_populates="lead", cascade="all, delete-orphan")
    appointments = relationship("TNAppointment", back_populates="lead", cascade="all, delete-orphan")


class TNConversation(Base):
    """Stores individual conversation sessions with a lead."""
    __tablename__ = "tn_conversations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("tn_leads.id"), nullable=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    overall_sentiment = Column(String(16), nullable=True)  # Positive, Neutral, Negative

    lead = relationship("TNLead", back_populates="conversations")
    messages = relationship("TNMessage", back_populates="conversation", cascade="all, delete-orphan")


class TNMessage(Base):
    """Individual chat message in a conversation."""
    __tablename__ = "tn_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("tn_conversations.id"), nullable=False)
    sender = Column(String(16), nullable=False)      # 'user' or 'agent'
    text = Column(Text, nullable=False)
    sentiment = Column(String(16), nullable=True)    # Positive, Neutral, Negative
    sentiment_score = Column(Float, default=0.0)     # -1.0 to 1.0
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("TNConversation", back_populates="messages")


class TNAppointment(Base):
    """Demo appointment bookings."""
    __tablename__ = "tn_appointments"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("tn_leads.id"), nullable=True)
    customer_name = Column(String(128), nullable=False)
    customer_email = Column(String(128), nullable=False)
    appointment_date = Column(String(32), nullable=False)   # stored as string for flexibility
    appointment_time = Column(String(16), nullable=False)
    product_interest = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(32), default="Scheduled")       # Scheduled, Completed, Cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("TNLead", back_populates="appointments")


class TNCallReport(Base):
    """Post-call summary and report."""
    __tablename__ = "tn_call_reports"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("tn_conversations.id"), nullable=True)
    lead_name = Column(String(128), nullable=True)
    summary = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    products_discussed = Column(String(256), nullable=True)
    sentiment = Column(String(16), nullable=True)
    lead_status = Column(String(16), nullable=True)
    next_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
