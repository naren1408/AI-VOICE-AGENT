import re
from typing import Dict, Any
from pydantic import BaseModel, Field

# --- LEAD SCORING WEIGHTS (Single dictionary for live-coding clarity) ---
LEAD_SCORING_WEIGHTS = {
    "budget_present": 25,          # Customer shared explicit budget or tier preference
    "timeline_urgent": 25,         # Buying timeline within 3-6 months or immediate
    "decision_maker": 25,          # User confirms they have decision or authority
    "need_clarity": 15,            # Specific pain point mentioned (cloud cost, FinOps, kubernetes)
    "contact_info_present": 10     # Valid email or phone provided
}

HOT_THRESHOLD = 70
WARM_THRESHOLD = 40


class LeadQualificationData(BaseModel):
    """Pydantic model for validated lead fields."""
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    need: str = ""
    budget: str = ""
    timeline: str = ""
    is_decision_maker: bool = False


def calculate_lead_score(lead: LeadQualificationData) -> int:
    """Calculate 0-100 score based on explicit rule weights."""
    score = 0

    # Budget score (+25)
    if lead.budget and len(lead.budget.strip()) > 1 and "not" not in lead.budget.lower():
        score += LEAD_SCORING_WEIGHTS["budget_present"]

    # Timeline score (+25)
    urgent_keywords = ["immediate", "now", "month", "quarter", "q1", "q2", "q3", "q4", "soon", "urgent", "202"]
    if lead.timeline and any(kw in lead.timeline.lower() for kw in urgent_keywords):
        score += LEAD_SCORING_WEIGHTS["timeline_urgent"]

    # Decision maker (+25)
    if lead.is_decision_maker:
        score += LEAD_SCORING_WEIGHTS["decision_maker"]

    # Need clarity (+15)
    if lead.need and len(lead.need.strip()) > 5:
        score += LEAD_SCORING_WEIGHTS["need_clarity"]

    # Contact info (+10)
    if (lead.email and "@" in lead.email) or (lead.phone and len(lead.phone.strip()) >= 8):
        score += LEAD_SCORING_WEIGHTS["contact_info_present"]

    return min(100, max(0, score))


def get_qualification_status(score: int) -> str:
    """Categorize lead as HOT, WARM, or COLD."""
    if score >= HOT_THRESHOLD:
        return "HOT"
    if score >= WARM_THRESHOLD:
        return "WARM"
    return "COLD"


def extract_lead_rule_based(conversation_text: str) -> LeadQualificationData:
    """Fast regex and keyword fallback extraction for Demo Mode without LLM API."""
    text = conversation_text.lower()
    data = LeadQualificationData()

    # Extract email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", conversation_text)
    if email_match:
        data.email = email_match.group(0)

    # Extract phone
    phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", conversation_text)
    if phone_match:
        data.phone = phone_match.group(0)

    # Extract budget (e.g. '$1,499', '$500', '1500', 'starter', 'professional', 'enterprise')
    budget_match = re.search(r"(\$[\d,]+|\b\d{3,6}\b|\b(?:starter|professional|enterprise|budget\s*of\s*[\w\d]+)\b)", conversation_text, re.IGNORECASE)
    if budget_match:
        data.budget = budget_match.group(0)

    # Timeline detection
    timeline_match = re.search(r"\b(immediately|urgent|next month|this month|this quarter|next quarter|in \d+ months?|q[1-4]|soon)\b", text)
    if timeline_match:
        data.timeline = timeline_match.group(0)

    # Decision maker detection
    if any(phrase in text for phrase in ["cto", "vp", "director", "head of", "decision maker", "i decide", "founder", "ceo", "manager"]):
        data.is_decision_maker = True

    # Need detection
    if "cost" in text or "save" in text or "cloud" in text or "aws" in text or "kubernetes" in text or "waste" in text:
        data.need = "Cloud compute optimization & FinOps cost reduction"

    # Name detection (e.g. 'my name is John' or 'I am Sarah')
    name_match = re.search(r"(?:my name is|i am|this is)\s+([A-Za-z]+)", conversation_text, re.IGNORECASE)
    if name_match:
        data.name = name_match.group(1).capitalize()

    # Company detection
    company_match = re.search(r"(?:from|at|company is)\s+([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)?)", conversation_text, re.IGNORECASE)
    if company_match:
        data.company = company_match.group(1).title()

    return data
