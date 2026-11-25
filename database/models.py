import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database.db import Base


class Lead(Base):
    """Stores extracted lead qualification data and scores."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=True)
    email = Column(String(128), unique=True, index=True, nullable=True)
    phone = Column(String(32), nullable=True)
    company = Column(String(128), nullable=True)
    need = Column(Text, nullable=True)
    budget = Column(String(64), nullable=True)
    timeline = Column(String(64), nullable=True)
    is_decision_maker = Column(Boolean, default=False)
    score = Column(Integer, default=0)
    qualification_status = Column(String(16), default="COLD")  # HOT, WARM, COLD
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    appointments = relationship("Appointment", back_populates="lead")


class Call(Base):
    """Tracks a single customer interaction session."""
    __tablename__ = "calls"

    id = Column(String(64), primary_key=True, index=True)  # unique call ID
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    language = Column(String(16), default="en")
    summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)
    objections = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    final_sentiment = Column(String(16), nullable=True)
    final_score = Column(Integer, default=0)

    messages = relationship("Message", back_populates="call", cascade="all, delete-orphan")


class Message(Base):
    """Stores conversation turns, latency metrics and sentiment per turn."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(64), ForeignKey("calls.id"), nullable=False, index=True)
    sender = Column(String(16), nullable=False)  # 'user' or 'agent'
    text = Column(Text, nullable=False)
    sentiment_label = Column(String(16), nullable=True)  # positive, neutral, negative
    sentiment_score = Column(Float, default=0.0)  # -1.0 to 1.0
    stt_latency_ms = Column(Integer, default=0)
    llm_latency_ms = Column(Integer, default=0)
    tts_latency_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    call = relationship("Call", back_populates="messages")


class Appointment(Base):
    """Stores booked product demos with conflict prevention."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    call_id = Column(String(64), nullable=True, index=True)
    customer_name = Column(String(128), nullable=False)
    customer_email = Column(String(128), nullable=False)
    slot_time = Column(DateTime, unique=True, nullable=False, index=True)  # Prevent double-booking
    status = Column(String(32), default="CONFIRMED")  # CONFIRMED, CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    lead = relationship("Lead", back_populates="appointments")
